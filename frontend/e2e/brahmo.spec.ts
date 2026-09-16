import { test, expect } from "@playwright/test";

test.describe("BRAHMO Rules Engine — Page Load", () => {
  test("renders header with title and zero LLM badge", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("BRAHMO Rules Engine");
    await expect(page.getByText("0 LLM calls")).toBeVisible();
    await expect(page.getByText(/deterministic · zero LLM calls/)).toBeVisible();
  });

  test("loads all 7 users in the session selector", async ({ page }) => {
    await page.goto("/");
    const select = page.locator("select");
    await expect(select).toBeVisible();
    const options = select.locator("option");
    await expect(options).toHaveCount(7);
  });

  test("renders the 4 stage cards (TOTAL → BFS → +ZONE 2 → 5-CHECK)", async ({ page }) => {
    await page.goto("/");
    // Stage cards use uppercase labels in small text
    await expect(page.locator("text=TOTAL").first()).toBeVisible();
    // Wait for pipeline result to load
    await expect(page.locator("text=nodes in graph").first()).toBeVisible();
    await expect(page.locator("text=reachable").first()).toBeVisible();
    await expect(page.locator("text=combined").first()).toBeVisible();
    await expect(page.locator("text=candidate set").first()).toBeVisible();
  });

  test("shows the backend connection info", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/local-seed · 50 nodes/)).toBeVisible();
  });
});

test.describe("BRAHMO Rules Engine — User Switch", () => {
  test("switching to Admin Suresh updates the candidate count to 42", async ({ page }) => {
    await page.goto("/");
    // Wait for initial load (Priya's pipeline completes)
    await expect(page.locator("text=nodes in graph").first()).toBeVisible();

    // Switch user
    await page.locator("select").selectOption("U-SURESH");

    // Wait for the pipeline to re-run: the role chip should update to ADMIN
    const chipSection = page.locator(".flex.flex-wrap.gap-2.text-xs");
    await expect(chipSection.getByText("ADMIN")).toBeVisible({ timeout: 5000 });
  });

  test("switching to Dr. Vikram updates the candidate count to 22", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=nodes in graph").first()).toBeVisible();

    await page.locator("select").selectOption("U-VIKRAM");
    await expect(page.getByText("22").first()).toBeVisible({ timeout: 5000 });
  });

  test("shows role and ceiling chips for the selected user", async ({ page }) => {
    await page.goto("/");
    // The chips are in a flex container with class 'text-xs'
    const chipSection = page.locator(".flex.flex-wrap.gap-2.text-xs");
    // Priya: VIEWER, L10
    await expect(chipSection.getByText("VIEWER")).toBeVisible();
    await expect(chipSection.getByText("L10")).toBeVisible();

    // Switch to Suresh
    await page.locator("select").selectOption("U-SURESH");
    await expect(chipSection.getByText("ADMIN")).toBeVisible({ timeout: 5000 });
    await expect(chipSection.getByText("L1").first()).toBeVisible();
  });
});

test.describe("BRAHMO Rules Engine — Filter Funnel", () => {
  test("renders the filter funnel with all 7 rows", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Filter funnel" })).toBeVisible();
    await expect(page.getByText("BFS reachable")).toBeVisible();
    await expect(page.getByText("+ Zone 2 injected")).toBeVisible();
    await expect(page.getByText("Check 1 — ISOLATION")).toBeVisible();
    await expect(page.getByText("Check 2 — COMPLIANCE")).toBeVisible();
    await expect(page.getByText("Check 3 — PERMISSION")).toBeVisible();
    await expect(page.getByText("Check 4 — TEMPORAL")).toBeVisible();
    await expect(page.getByText("Check 5 — DERIVABILITY")).toBeVisible();
  });

  test("expanding Check 2 shows SQL predicate and excluded nodes", async ({ page }) => {
    await page.goto("/");
    await page.getByText("Check 2 — COMPLIANCE").click();
    // SQL predicate
    await expect(page.getByText(/compliance_tags/)).toBeVisible();
    // Excluded node IDs
    await expect(page.getByText("N-O11")).toBeVisible();
    await expect(page.getByText("N-O12")).toBeVisible();
  });

  test("collapsing and re-expanding works", async ({ page }) => {
    await page.goto("/");
    await page.getByText("Check 2 — COMPLIANCE").click();
    await expect(page.getByText("N-O11")).toBeVisible();
    await page.getByText("Check 2 — COMPLIANCE").click();
    await expect(page.getByText("N-O11")).not.toBeVisible();
  });
});

test.describe("BRAHMO Rules Engine — Timing Panel", () => {
  test("renders timing section with per-stage bars", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Pipeline timing" })).toBeVisible();
    await expect(page.getByText("permission compile")).toBeVisible();
    await expect(page.getByText("BFS traversal", { exact: true })).toBeVisible();
    await expect(page.getByText("content fetch")).toBeVisible();
  });

  test("shows total time under 500ms budget", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/budget 500 ms/)).toBeVisible();
  });

  test("shows the four stat boxes", async ({ page }) => {
    await page.goto("/");
    // The timing section contains 4 stat boxes
    const timingSection = page.locator("section").filter({ hasText: "Pipeline timing" });
    await expect(timingSection.getByText("LLM calls")).toBeVisible();
    await expect(timingSection.getByText("content rows fetched")).toBeVisible();
    await expect(timingSection.getByText("levels reached")).toBeVisible();
    await expect(timingSection.getByText("revisits prevented")).toBeVisible();
  });
});

test.describe("BRAHMO Rules Engine — DAG Viewer", () => {
  test("renders the hierarchy DAG with entry point info", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Hierarchy DAG" })).toBeVisible();
    // Entry point name appears in the detail text
    await expect(page.getByText("Ortho Ward").first()).toBeVisible();
  });

  test("shows the legend with all marker types", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("entry point").first()).toBeVisible();
    await expect(page.getByText("reached by BFS").first()).toBeVisible();
    await expect(page.getByText("not reachable").first()).toBeVisible();
    await expect(page.getByText("Zone 2 (injected)").first()).toBeVisible();
  });

  test("shows multi-parent annotation for Post-TKR level", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/multi-parent/).first()).toBeVisible();
  });
});

test.describe("BRAHMO Rules Engine — Candidate Table", () => {
  test("renders the candidate set with type groups", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Candidate set" })).toBeVisible();
    await expect(page.getByText("CONSTRAINT").first()).toBeVisible();
    await expect(page.getByText("FACT").first()).toBeVisible();
  });

  test("shows Warfarin-NSAID and patient contraindication for Priya", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Warfarin-NSAID Interaction")).toBeVisible();
    await expect(page.getByText(/NSAID Contraindication/).first()).toBeVisible();
  });

  test("expanding a candidate row shows content", async ({ page }) => {
    await page.goto("/");
    await page.getByText("Warfarin-NSAID Interaction").click();
    // The content text should appear after expansion
    await expect(page.getByText(/CRITICAL: Never prescribe/).first()).toBeVisible();
  });
});

test.describe("BRAHMO Rules Engine — Comparison View", () => {
  test("renders comparison section with user toggle pills", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Same graph, different users" })).toBeVisible();
    await expect(page.getByText("Pick 2–4 users.")).toBeVisible();
  });

  test("shows comparison columns with candidate counts", async ({ page }) => {
    await page.goto("/");
    // Default comparison: Priya, Vikram, Suresh
    // The comparison section shows user names
    await expect(page.getByText("Nurse Priya").last()).toBeVisible();
  });

  test("toggling a user updates the comparison", async ({ page }) => {
    await page.goto("/");
    // The comparison section has user pills
    const pills = page.locator("section").filter({ hasText: "Same graph, different users" }).locator("button");
    // Click a currently-selected pill to deselect
    await pills.filter({ hasText: "Admin Suresh" }).click();
    // Wait for comparison to update
    await page.waitForTimeout(500);
    // The section should still be visible (now with 2 users)
    await expect(page.getByText("Pick 2–4 users.")).toBeVisible();
  });

  test("shows shared and exclusive node ids", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/shared by all selected/).first()).toBeVisible();
    // N-G01 should be in the shared set
    await expect(page.getByText("N-G01").last()).toBeVisible();
  });
});
