import { ButtonLink } from "@/components/ui/button-link";

export function ErrorNotice({ message }: { message: string }) {
  const needsAuth = /authentication|credentials|not authenticated/i.test(message);
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <p className="text-pretty">{needsAuth ? "Sign in to see your personalised learning data." : message}</p>
      {needsAuth && (
        <ButtonLink href="/login" size="sm" className="mt-3">
          Sign in
        </ButtonLink>
      )}
    </div>
  );
}
