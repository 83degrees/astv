export const PANEL_PATH = "/astv-intent-catalogue";

export function classifyAuthenticationState({ authenticated, error }) {
  if (authenticated) return "authenticated";
  if (error) return "authentication_error";
  return "pending";
}

export function requireNativeUnauthorized(result) {
  if (result?.kind !== "backend_denial") {
    throw new Error(`Expected backend denial; received ${result?.kind ?? "missing result"}`);
  }
  if (result.code !== "unauthorized") {
    throw new Error(`Expected native unauthorized denial; received ${result.code || "missing code"}`);
  }
}
