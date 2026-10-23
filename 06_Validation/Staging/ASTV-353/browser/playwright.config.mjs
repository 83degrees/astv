export default {
  testDir: "/work",
  timeout: 60000,
  retries: 0,
  workers: 1,
  reporter: [["json", { outputFile: "/evidence/browser-results.json" }], ["line"]],
  use: { browserName: "chromium", ignoreHTTPSErrors: false, trace: "retain-on-failure" },
};
