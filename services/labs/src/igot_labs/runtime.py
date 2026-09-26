from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor,TimeoutError as FutureTimeout
from base64 import b64decode
from io import BytesIO
from pathlib import PurePosixPath
import tarfile
import docker
from docker.errors import DockerException,NotFound
from .config import get_settings
class RuntimeUnavailable(RuntimeError):pass
@dataclass
class Provisioned:
    workspace_id:str;target_ids:list[str];network_id:str;workspace_host:str;public_port:int|None=None
class DockerRuntime:
    def __init__(self,client=None):
        cfg=get_settings()
        try:self.client=client or docker.DockerClient(base_url=cfg.docker_base_url)
        except DockerException as exc:raise RuntimeUnavailable(str(exc))
    def health(self):
        try:return self.client.ping()
        except DockerException as exc:raise RuntimeUnavailable(str(exc))
    def connect_controller(self,network_id:str):
        try:
            network=self.client.networks.get(network_id);network.reload()
            if not any(container.name==get_settings().controller_container_name for container in network.containers):
                network.connect(get_settings().controller_container_name)
        except DockerException as exc:raise RuntimeUnavailable(str(exc)) from exc
    def provision(self,session_id:str,target_images:list[str],challenge:dict|None=None)->Provisioned:
        cfg=get_settings();unknown=set(target_images)-cfg.target_allowlist
        if unknown:raise ValueError(f"target image is not allowed: {sorted(unknown)}")
        labels={"igot.lab.session":session_id};network=None;created=[]
        try:
            network=self.client.networks.create(f"igot-lab-{session_id}",driver="bridge",internal=True,labels=labels)
            for index,image in enumerate(target_images):
                target=self.client.containers.run(image,detach=True,network=network.name,name=f"igot-target-{session_id}-{index}",labels=labels,mem_limit="256m",nano_cpus=500_000_000,pids_limit=128,read_only=True,security_opt=["no-new-privileges:true"],cap_drop=["ALL"],tmpfs={"/tmp":"rw,noexec,nosuid,size=32m"});created.append(target)
            workspace=self.client.containers.run(cfg.workspace_image,detach=True,network=network.name,name=f"igot-workspace-{session_id}",labels=labels,mem_limit="512m",nano_cpus=1_000_000_000,pids_limit=256,read_only=not bool(challenge),security_opt=["no-new-privileges:true"],cap_drop=["ALL"],tmpfs={"/tmp":"rw,noexec,nosuid,size=64m","/workspace":"rw,nosuid,size=256m"},**({"command":["sleep","infinity"]} if challenge else {}))
            created.append(workspace)
            public_port=None
            if challenge:
                archive=self._challenge_archive(challenge)
                if not workspace.put_archive("/opt/lab",archive):raise RuntimeUnavailable("Could not install challenge materials")
                command=f"python -m marimo run /opt/lab/challenge.py --host 0.0.0.0 --port 2718 --no-token --headless --no-skew-protection --base-url {challenge['console_base']} --allow-origins '*' > /tmp/marimo-launch.log 2>&1"
                workspace.exec_run(["sh","-c",command],detach=True,user="learner",workdir="/opt/lab")
            # The control service joins the private network and is the only proxy.
            try:network.connect(cfg.controller_container_name)
            except (DockerException,NotFound):pass # local host-mode development
            return Provisioned(workspace.id,[c.id for c in created[:-1]],network.id,workspace.name,public_port)
        except Exception:
            for container in reversed(created):
                try:container.remove(force=True)
                except Exception:pass
            if network:
                try:network.remove()
                except Exception:pass
            raise
    @staticmethod
    def _challenge_archive(challenge:dict)->bytes:
        notebook=str(challenge.get("notebook_code") or "")
        if not notebook.strip().startswith("import marimo") or len(notebook)>200_000:raise ValueError("Challenge notebook is unavailable")
        payloads={"challenge.py":notebook.encode("utf-8")}
        for name,value in (challenge.get("artifacts") or {}).items():
            path=PurePosixPath(str(name))
            if path.is_absolute() or ".." in path.parts or len(path.parts)>5:raise ValueError("Unsafe challenge artifact path")
            data=b64decode(value[7:]) if isinstance(value,str) and value.startswith("base64:") else str(value).encode("utf-8")
            if len(data)>2_000_000:raise ValueError("Challenge artifact is too large")
            payloads[str(PurePosixPath("data")/path)]=data
        stream=BytesIO()
        with tarfile.open(fileobj=stream,mode="w") as archive:
            directories={str(PurePosixPath(path).parent) for path in payloads if "/" in path}
            for directory in sorted(directories,key=lambda item:item.count("/")):
                info=tarfile.TarInfo(directory+"/");info.type=tarfile.DIRTYPE;info.mode=0o755;archive.addfile(info)
            for path,data in payloads.items():
                info=tarfile.TarInfo(path);info.size=len(data);info.mode=0o644;archive.addfile(info,BytesIO(data))
        return stream.getvalue()
    def status(self,container_id:str)->str:
        try:c=self.client.containers.get(container_id);c.reload();return c.status
        except NotFound:return "missing"
        except DockerException as exc:raise RuntimeUnavailable(str(exc))
    def execute(self,container_id:str,argv:list[str])->dict:
        if not argv or len(argv)>32 or any(len(v)>16000 for v in argv):raise ValueError("invalid command arguments")
        try:
            container=self.client.containers.get(container_id)
            pool=ThreadPoolExecutor(max_workers=1)
            future=pool.submit(container.exec_run,argv,demux=True,user="learner",workdir="/workspace")
            try:result=future.result(timeout=get_settings().execution_timeout_seconds)
            except FutureTimeout:
                pool.shutdown(wait=False,cancel_futures=True)
                raise RuntimeUnavailable("execution exceeded time limit")
            else:
                pool.shutdown(wait=True)
            stdout,stderr=result.output;cap=get_settings().max_output_bytes
            return {"exit_code":result.exit_code,"stdout":(stdout or b"")[:cap].decode(errors="replace"),"stderr":(stderr or b"")[:cap].decode(errors="replace"),"truncated":len(stdout or b"")+len(stderr or b"")>cap*2}
        except DockerException as exc:raise RuntimeUnavailable(str(exc))
    def reset(self,container_id:str):
        try:self.client.containers.get(container_id).restart(timeout=5)
        except DockerException as exc:raise RuntimeUnavailable(str(exc))
    def terminate(self,workspace_id:str|None,target_ids:list[str],network_id:str|None):
        for cid in [workspace_id,*target_ids]:
            if not cid:continue
            try:self.client.containers.get(cid).remove(force=True)
            except NotFound:pass
        if network_id:
            try:
                network=self.client.networks.get(network_id)
                try:network.disconnect(get_settings().controller_container_name,force=True)
                except (DockerException,NotFound):pass
                network.remove()
            except NotFound:pass
    def archive(self,container_id:str,path:str="/workspace"):
        normalized=PurePosixPath(path)
        if ".." in normalized.parts or normalized.parts[:1]!=("/",) or normalized.parts[1:2]!=("workspace",):raise ValueError("only workspace artifacts may be collected")
        stream,stat=self.client.containers.get(container_id).get_archive(str(normalized));return b"".join(stream),stat
