import { test, expect, type Page } from "@playwright/test";
import fs from "node:fs";

async function login(page: Page, actor = "qc1") {
  await page.goto("/");
  await page.getByRole("combobox").selectOption(actor);
  await page.getByRole("button", { name: "進入工作區", exact: true }).click();
  await expect(page.locator(".mq-shell")).toBeVisible();
}

test("病例分頁、原文定位和返回條件保持", async ({ page }) => {
  await login(page);
  await expect(page.locator(".data-table tbody tr").first()).toBeVisible();
  fs.mkdirSync("../artifacts/verification/screenshots", { recursive: true });
  await page.screenshot({
    path: "../artifacts/verification/screenshots/workbench-final.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "下一頁", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
  await page.getByRole("button", { name: "打開病例 陳**" }).click();
  await expect(
    page.getByRole("heading", { name: "陳**的病歷質控" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../artifacts/verification/screenshots/case-final.png",
    fullPage: true,
  });
  await page
    .locator(".finding-item")
    .filter({ hasText: "過敏記載" })
    .first()
    .click();
  await page.locator(".evidence-quote").first().click();
  await expect(
    page.getByRole("dialog", { name: "固定版本原文" }),
  ).toBeVisible();
  await expect(page.locator(".highlighted-line")).toContainText("過敏");
  await page.getByRole("button", { name: "關閉", exact: true }).click();
  await page.getByRole("button", { name: "返回病例隊列", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
  await expect(
    page.getByRole("button", { name: "上一頁", exact: true }),
  ).toBeEnabled();
});

for (const viewport of [
  { width: 1440, height: 1000 },
  { width: 1280, height: 800 },
]) {
  test(`原生圖譜探索、路徑、主題與鍵盤 ${viewport.width}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await login(page);
    await page.getByRole("link", { name: "知識圖譜" }).click();
    await expect(page.getByTestId("ontology-graph-canvas")).toBeVisible();
    if (
      await page
        .getByRole("button", { name: "搜索與路徑", exact: true })
        .isVisible()
    )
      await page
        .getByRole("button", { name: "搜索與路徑", exact: true })
        .click();
    await page.getByPlaceholder("搜索名稱、定義與屬性").fill("臨床斷言");
    await page
      .locator(".search-result-item")
      .filter({ hasText: "臨床斷言" })
      .first()
      .click();
    await expect(page.locator(".graph-inspector")).toBeVisible();
    await expect(page.locator(".graph-inspector")).toContainText("臨床斷言");
    await page.getByPlaceholder("搜索名稱、定義與屬性").fill("");
    await page.getByRole("button", { name: "有向路徑", exact: true }).click();
    await page
      .locator(".pathfinder-select")
      .nth(0)
      .selectOption("ClinicalDocument");
    await page
      .locator(".pathfinder-select")
      .nth(1)
      .selectOption("EvidenceReference");
    await page.getByRole("button", { name: "查找路徑", exact: true }).click();
    await expect(page.locator(".pathfinder-chain")).toContainText("證據引用");
    await page
      .getByRole("combobox", { name: "圖譜主題" })
      .selectOption("aurora");
    await expect(page.locator(".native-workspace")).toHaveClass(/theme-aurora/);
    await page.keyboard.press("Meta+k");
    await expect(page.locator(".command-palette")).toBeVisible();
    await page.keyboard.press("Escape");
    fs.mkdirSync("../artifacts/verification/screenshots", { recursive: true });
    await page.screenshot({
      path: `../artifacts/verification/screenshots/graph-${viewport.width}.png`,
      fullPage: true,
    });
    expect(errors).toEqual([]);
  });
}

test("原生設計器保存、撤銷重做及候選恢復", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "知識圖譜" }).click();
  await page.getByRole("button", { name: "設計本體", exact: true }).click();
  await expect(page.locator(".designer-page")).toBeVisible();
  await page
    .locator(".designer-meta-desc")
    .fill("瀏覽器驗證：保留原生設計器與候選版本。");
  await page.getByRole("button", { name: "Undo (Ctrl+Z)" }).click();
  await page.getByRole("button", { name: "Redo (Ctrl+Shift+Z)" }).click();
  await page.getByRole("button", { name: "保存候選", exact: true }).click();
  await expect(page.locator(".graph-notice")).toContainText("候選已保存");
  await page.locator(".designer-back-btn").click();
  await page.getByRole("button", { name: "候選與審核", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("醫療病歷質控應用本體");
  await page
    .getByRole("button", { name: "繼續編輯", exact: true })
    .first()
    .click();
  await expect(page.locator(".designer-meta-desc")).toHaveValue(
    "瀏覽器驗證：保留原生設計器與候選版本。",
  );
});

test("病例證據圖回指同版本原文", async ({ page }) => {
  await login(page);
  await page.goto("/cases/C001");
  await page
    .locator(".finding-item")
    .filter({ hasText: "過敏記載" })
    .first()
    .click();
  await page.getByRole("button", { name: "查看證據關係", exact: true }).click();
  await expect(page).toHaveURL(/view=case/);
  await expect(page.getByTestId("ontology-graph-canvas")).toBeVisible();
  if (
    await page
      .getByRole("button", { name: "搜索與路徑", exact: true })
      .isVisible()
  )
    await page.getByRole("button", { name: "搜索與路徑", exact: true }).click();
  await page.getByPlaceholder("搜索名稱、定義與屬性").fill("青黴素");
  await page
    .locator(".search-result-item")
    .filter({ hasText: "青黴素" })
    .first()
    .click();
  const source = page.getByRole("button", {
    name: "並列查看原文",
    exact: true,
  });
  if (await source.count()) await source.click();
  else
    await page
      .getByRole("button", { name: "查看支持原文", exact: true })
      .first()
      .click();
  await expect(page.locator(".graph-evidence")).toContainText("青黴素");
  await page.getByRole("button", { name: "關閉原文", exact: true }).click();
  await page.getByRole("button", { name: "返回原任務", exact: true }).click();
  await expect(page).toHaveURL(/cases\/C001/);
});

test("規則、資料與權限頁使用真實服務", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "規則與依據", exact: true }).click();
  await expect(page.locator(".rules-list>button")).toHaveCount(8);
  await page
    .getByPlaceholder("按規則編號、術語或問題查找依據")
    .fill("MQC-DOC-005");
  await page.getByRole("button", { name: "檢索依據", exact: true }).click();
  await expect(page.locator(".retrieval-results")).toContainText(
    "編號精確定位",
  );
  await page.getByRole("link", { name: "資料接入", exact: true }).click();
  await expect(
    page.getByRole("cell", { name: "醫院結構化資料", exact: false }),
  ).toBeVisible();
  await page.getByRole("link", { name: "權限與審計", exact: true }).click();
  await expect(page.locator(".data-table tbody tr").first()).toBeVisible();
});

test("只擁有運行診斷權限的身份沒有病例入口", async ({ page }) => {
  await login(page, "support1");
  await expect(
    page.getByRole("link", { name: "質控工作臺", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("link", { name: "運行狀態", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "運行狀態", exact: true }),
  ).toBeVisible();
  await expect(page.locator("main")).toContainText("不包含病例正文");
  await page.goto("/cases/C001");
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.locator("main")).not.toContainText("青黴素");
});

test("千元素保留原生 grid 策略且第 100 項之後可定位", async ({ page }) => {
  await login(page);
  const native = await page.request.get("/api/v1/knowledge-graphs/views");
  const fixture = await native.json();
  fixture.ontology = {
    name: "合成規模夾具",
    description: "僅用於工程性能，不是真實病例數量",
    entityTypes: Array.from({ length: 500 }, (_, i) => ({
      id: "scale-" + i,
      name: "壓力樣本節點 " + i,
      description: "合成類型 " + i,
      properties: [],
      icon: "◇",
      color: "#4895dd",
    })),
    relationships: Array.from({ length: 500 }, (_, i) => ({
      id: "edge-" + i,
      name: "關聯",
      from: "scale-" + i,
      to: "scale-" + ((i + 1) % 500),
      cardinality: "many-to-many",
    })),
  };
  fixture.node_meta = Object.fromEntries(
    fixture.ontology.entityTypes.map((n: any) => [
      n.id,
      { semantic_kind: "class", source_role: "synthetic" },
    ]),
  );
  fixture.edge_meta = {};
  fixture.loaded_counts = { nodes: 500, edges: 500 };
  await page.route("**/api/v1/knowledge-graphs/views?*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(fixture),
    }),
  );
  const start = Date.now();
  await page.goto("/graph");
  await expect(
    page.getByText("Large ontology: using the fast grid layout"),
  ).toBeVisible();
  const interactive = Date.now() - start;
  await page.getByPlaceholder("搜索名稱、定義與屬性").fill("壓力樣本節點 499");
  const lookup = Date.now();
  await page
    .getByRole("button", { name: "壓力樣本節點 499", exact: true })
    .click();
  await expect(page.locator(".graph-inspector")).toContainText(
    "壓力樣本節點 499",
  );
  const selection = Date.now() - lookup;
  expect(interactive).toBeLessThan(5000);
  expect(selection).toBeLessThan(1000);
  const measurements = [
    { interactive_ms: interactive, selection_ms: selection, js_heap_bytes: 0 },
  ];
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Performance.enable");
  measurements[0].js_heap_bytes = (
    await cdp.send("Performance.getMetrics")
  ).metrics.find((m: { name: string }) => m.name === "JSHeapUsedSize")!.value;
  // The design calls for percentile and memory observations, beyond a single smoke measurement.
  for (let i = 1; i < 15; i++) {
    const begin = Date.now();
    await page.reload();
    await expect(
      page.getByText("Large ontology: using the fast grid layout"),
    ).toBeVisible();
    const ready = Date.now() - begin;
    await page
      .getByPlaceholder("搜索名稱、定義與屬性")
      .fill("壓力樣本節點 499");
    const selectedAt = Date.now();
    await page
      .getByRole("button", { name: "壓力樣本節點 499", exact: true })
      .click();
    await expect(page.locator(".graph-inspector")).toContainText(
      "壓力樣本節點 499",
    );
    const delay = Date.now() - selectedAt;
    const heap = (await cdp.send("Performance.getMetrics")).metrics.find(
      (m: { name: string }) => m.name === "JSHeapUsedSize",
    )!.value;
    measurements.push({
      interactive_ms: ready,
      selection_ms: delay,
      js_heap_bytes: heap,
    });
    expect(ready).toBeLessThan(5000);
    expect(delay).toBeLessThan(1000);
  }
  await cdp.detach();
  const percentile = (key: "interactive_ms" | "selection_ms", q: number) =>
    [...measurements].map((m) => m[key]).sort((a, b) => a - b)[
      Math.ceil(q * measurements.length) - 1
    ];
  fs.writeFileSync(
    "../artifacts/verification/graph-performance.json",
    JSON.stringify(
      {
        fixture: "synthetic-500-nodes-500-edges",
        viewport: { width: 1440, height: 1000 },
        interactive_ms: interactive,
        selection_ms: selection,
        observations: measurements,
        repeated_loads: measurements.length,
        interactive_p50_ms: percentile("interactive_ms", 0.5),
        interactive_p95_ms: percentile("interactive_ms", 0.95),
        selection_p50_ms: percentile("selection_ms", 0.5),
        selection_p95_ms: percentile("selection_ms", 0.95),
        peak_js_heap_bytes: Math.max(
          ...measurements.map((m) => m.js_heap_bytes),
        ),
        memory_scope:
          "Chrome DevTools JSHeapUsedSize；不包含瀏覽器/Canvas 原生總內存，不是長時洩漏檢查",
        engineering_budget: { interactive_ms: 5000, selection_ms: 1000 },
        production_sla: false,
      },
      null,
      2,
    ),
  );
});
