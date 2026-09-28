export default function OfflinePage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center gap-3 px-4 text-zinc-100">
      <h1 className="text-2xl font-bold">You’re offline</h1>
      <p className="text-sm text-zinc-400">
        DeepLM’s shell is cached, but grammar and tenses need a network connection
        to the API.
      </p>
      <a href="/" className="text-sm text-blue-400 underline">
        Try again
      </a>
    </main>
  );
}
