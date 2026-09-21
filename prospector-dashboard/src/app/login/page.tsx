export const dynamic = "force-dynamic";

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const params = await searchParams;
  return (
    <main className="login">
      <div className="card">
        <span className="badge">PRIVATE ACCESS</span>
        <h1>Prospector</h1>
        <p className="subtle">Single-operator access. Public signup is not available.</p>
        {params.error && <p className="error">Login failed.</p>}
        <form action="/api/auth/login" method="post">
          <label>Email<input name="email" type="email" autoComplete="username" required /></label>
          <label>Password<input name="password" type="password" autoComplete="current-password" required /></label>
          <button className="button primary" type="submit">Entrar</button>
        </form>
      </div>
    </main>
  );
}
