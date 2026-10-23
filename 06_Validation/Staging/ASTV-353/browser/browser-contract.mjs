export const PANEL_PATH = "/astv-intent-catalogue";

export function classifyAuthenticationState({ authenticated, error }) {
  if (authenticated) return "authenticated";
  if (error) return "authentication_error";
  return "pending";
}

export function permissionProbeRequest() {
  return {
    type: "call_service",
    domain: "astv_intent_catalogue",
    service: "validate_intent_record",
    service_data: {
      intent_id: "astv353_validation",
      record: {
        intent: "media.play_source",
        title: "ASTV 353 validation media",
        params: {
          output: { domain: "audio" },
          catalogue_id: "astv_353_stage",
          item_id: "validation_media",
        },
      },
    },
    return_response: true,
  };
}

export function requireBackendUnauthorizedProof(result) {
  if (result?.kind !== "backend_denial") {
    throw new Error(`Expected backend denial; received ${result?.kind ?? "missing result"}`);
  }
  if (result.code === "unauthorized") {
    return { status: "passed", proof: "native_error_code" };
  }
  if (result.code === "home_assistant_error") {
    return { status: "pending_backend_log", proof: "exact_service_unauthorized_log" };
  }
  throw new Error(`Expected an authorization-denial error; received ${result.code || "missing code"}`);
}
