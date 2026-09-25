from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor,TimeoutError as FutureTimeout
from pathlib import PurePosixPath
import docker
from docker.errors import DockerException,NotFound
from .config import get_settings
class RuntimeUnavailable(RuntimeError):pass
@dataclass
class Provisioned:
    workspace_id:str;target_ids:list[str];network_id:str;workspace_host:str
class DockerRuntime:
    def __init__(self,client=None):
        cfg=get_settings()
        try:self.client=client or docker.DockerClient(base_url=cfg.docker_base_url)
        except DockerException as exc:raise RuntimeUnavailable(str(exc))
    def health(self):
        try:return self.client.ping()
        except DockerException as exc:raise RuntimeUnavailable(str(exc))
    def provision(self,session_id:str,target_images:list[str])->Provisioned:
        cfg=get_settings();unknown=set(target_images)-cfg.target_allowlist
        if unknown:raise ValueError(f"target image is not allowed: {sorted(unknown)}")
        labels={"igot.lab.session":session_id};network=None;created=[]
        try:
            network=self.client.networks.create(f"igot-lab-{session_id}",driver="bridge",internal=True,labels=labels)
            for index,image in enumerate(target_images):
                target=self.client.containers.run(image,detach=True,network=network.name,name=f"igot-target-{session_id}-{index}",labels=labels,mem_limit="256m",nano_cpus=500_000_000,pids_limit=128,read_only=True,security_opt=["no-new-privileges:true"],cap_drop=["ALL"],tmpfs={"/tmp":"rw,noexec,nosuid,size=32m"});created.append(target)
            workspace=self.client.containers.run(cfg.workspace_image,detach=True,network=network.name,name=f"igot-workspace-{session_id}",labels=labels,mem_limit="512m",nano_cpus=1_000_000_000,pids_limit=256,read_only=True,security_opt=["no-new-privileges:true"],cap_drop=["ALL"],tmpfs={"/tmp":"rw,noexec,nosuid,size=64m","/workspace":"rw,nosuid,size=256m"})
            created.append(workspace)
            # The control service joins the private network and is the only proxy.
            try:network.connect(cfg.controller_container_name)
            except (DockerException,NotFound):pass # local host-mode development
            return Provisioned(workspace.id,[c.id for c in created[:-1]],network.id,workspace.name)
        except Exception:
            for container in reversed(created):
                try:container.remove(force=True)
                except Exception:pass
            if network:
                try:network.remove()
                except Exception:pass
            raise
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
