import { test, expect, type Page } from "@playwright/test";
import fs from "node:fs";

async function login(page: Page, actor: string) {
  await page.goto("/");
  await page.getByRole("combobox").selectOption(actor);
  await page.getByRole("button", { name: "進入工作區", exact: true }).click();
  await expect(page.locator(".mq-shell")).toBeVisible();
}

test("固定評測、未滿足准入和工程資產交接可連續操作", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await login(page, "qc1");
  await expect(page.locator(".data-table tbody tr").first()).toBeVisible();
  fs.mkdirSync("../artifacts/verification/screenshots", { recursive: true });
  await page.screenshot({
    path: "../artifacts/verification/screenshots/workbench-final.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "專家評測", exact: true }).click();
  await page.getByRole("button", { name: "創建評測批次", exact: true }).click();
  await page.getByLabel("批次名稱").fill("本地流程核對 · 固定樣本待專家評測");
  await page.locator(".case-picks input[type=checkbox]").first().check();
  await page
    .getByRole("button", { name: "凍結樣本並創建", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "證據與建議分項", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".metric-panel")).toContainText("未定義");
  await expect(
    page.locator(".eval-stats .stat").last().locator("strong"),
  ).toHaveText("8");
  await page
    .getByRole("button", { name: "查看與評價", exact: true })
    .first()
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.locator(".modal-context")).toContainText("MQC-DOC");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.screenshot({
    path: "../artifacts/verification/screenshots/evaluation-final.png",
    fullPage: true,
  });
  await page.locator(".account").click();
  await login(page, "manager1");
  await page.getByRole("link", { name: "評測與准入", exact: true }).click();
  await page.getByRole("button", { name: "建立准入申請", exact: true }).click();
  await page
    .getByRole("button", { name: "創建並檢查缺項", exact: true })
    .click();
  await expect(page.locator(".gate-condition").first()).toContainText("未滿足");
  await page
    .getByLabel("本次責任意見")
    .fill("本地工程走查：沒有專業樣本與責任條件，保持阻斷。");
  await page
    .getByRole("button", { name: "核對全部條件並記錄決定", exact: true })
    .click();
  await expect(page.locator(".batch-selector")).toContainText("待補充依據");
  await page.getByRole("link", { name: "交付資產", exact: true }).click();
  await page.locator(".export-builder select").selectOption({ index: 1 });
  await page.getByRole("button", { name: "生成交接包", exact: true }).click();
  await expect(page.locator(".data-table tbody tr").first()).toContainText(
    "未獲臨床放行",
  );
  await page.getByRole("button", { name: "清單", exact: true }).first().click();
  await expect(page.getByRole("dialog")).toContainText("ontology/shapes.ttl");
  await expect(page.getByRole("dialog")).toContainText("參考答案/留出標註");
  expect(errors).toEqual([]);
});

test("圖接口故障後可返回原任務並在同範圍恢復", async ({ page }) => {
  await login(page, "qc1");
  await page.route("**/api/v1/knowledge-graphs/views?*", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "fixture_unavailable",
          message: "工程故障夾具：當前圖服務不可用",
        },
      }),
    }),
  );
  await page.goto("/graph?view=case&case=C001&return=%2Fcases%2FC001");
  await expect(page.getByRole("alert")).toContainText("當前圖服務不可用");
  await expect(page.getByTestId("ontology-graph-canvas")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "返回原任務", exact: true }),
  ).toBeVisible();
  await page.unroute("**/api/v1/knowledge-graphs/views?*");
  await page.getByRole("button", { name: "重試當前圖譜", exact: true }).click();
  await expect(page.getByTestId("ontology-graph-canvas")).toBeVisible();
  await expect(page).toHaveURL(/case=C001/);
  await page.getByRole("button", { name: "返回原任務", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "陳**的病歷質控" }),
  ).toBeVisible();
});

test("候選保存失敗不丟輸入且退出可以取消", async ({ page }) => {
  await login(page, "qc1");
  await page.getByRole("link", { name: "知識圖譜" }).click();
  await page.getByRole("button", { name: "設計本體", exact: true }).click();
  const description = page.locator(".designer-meta-desc");
  await description.fill("工程故障夾具：未保存的新定義不能丟失。");
  await page.route("**/api/v1/knowledge-graphs/drafts", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "fixture_save_failure",
          message: "工程故障夾具：保存暫不可用",
        },
      }),
    }),
  );
  await page.getByRole("button", { name: "保存候選", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("保存暫不可用");
  await expect(description).toHaveValue(
    "工程故障夾具：未保存的新定義不能丟失。",
  );
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.locator(".designer-back-btn").click();
  await expect(description).toBeVisible();
  await page.unroute("**/api/v1/knowledge-graphs/drafts");
  await page.getByRole("button", { name: "保存候選", exact: true }).click();
  await expect(page.locator(".graph-notice")).toContainText("候選已保存");
});

test("舊圖響應晚到不能覆蓋當前視圖", async ({ page }) => {
  await login(page, "qc1");
  const old = await (
    await page.request.get("/api/v1/knowledge-graphs/views?view_kind=ontology")
  ).json();
  old.ontology.entityTypes[0].name = "過期響應不得進入當前圖";
  const current = await (
    await page.request.get("/api/v1/knowledge-graphs/views?view_kind=rule")
  ).json();
  let releaseOld!: () => void;
  const held = new Promise<void>((resolve) => {
    releaseOld = resolve;
  });
  let intercepted!: () => void;
  const arrived = new Promise<void>((resolve) => {
    intercepted = resolve;
  });
  await page.route("**/api/v1/knowledge-graphs/views?*", async (route) => {
    if (
      new URL(route.request().url()).searchParams.get("view_kind") ===
      "ontology"
    ) {
      intercepted();
      await held;
      await route
        .fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(old),
        })
        .catch(() => {});
    } else await route.continue();
  });
  await page.goto("/graph");
  await arrived;
  await page.getByRole("button", { name: "規則影響", exact: true }).click();
  await expect(page.getByTestId("ontology-graph-canvas")).toBeVisible();
  await expect(page.locator(".graph-statusbar")).toContainText(
    current.loaded_counts.nodes + " 個節點",
  );
  releaseOld();
  await page
    .getByPlaceholder("搜索名稱、定義與屬性")
    .fill("過期響應不得進入當前圖");
  await expect(page.locator(".search-result-item")).toHaveCount(0);
  await expect(page.locator(".graph-statusbar")).toContainText(
    current.loaded_counts.nodes + " 個節點",
  );
});

test("掃描表格證據能回看帶頁框的旋轉原圖", async ({ page }) => {
  await login(page, "qc1");
  await page.getByRole("link", { name: "資料接入", exact: true }).click();
  const row = page
    .locator(".data-table tbody tr")
    .filter({ hasText: "工程混合與旋轉掃描" });
  await row.getByRole("button", { name: "查看", exact: true }).click();
  await page
    .getByRole("button", { name: "查看解析證據與病例接入", exact: true })
    .click();
  const table = page
    .locator(".source-record")
    .filter({ hasText: "表格" })
    .filter({ hasText: "0007" });
  await expect(table).toHaveCount(1);
  await table
    .getByRole("button", { name: "查看第 3 頁原圖與位置", exact: true })
    .click();
  await expect(table.locator("img")).toBeVisible();
  await expect
    .poll(() =>
      table
        .locator("img")
        .evaluate(
          (img: HTMLImageElement) => img.complete && img.naturalWidth > 0,
        ),
    )
    .toBe(true);
  await table.getByRole("button", {name:"向左旋轉視圖",exact:true}).click();
  await expect(table.locator("img")).toHaveAttribute("data-view-rotation", "270");
  await page.screenshot({
    path: "../artifacts/verification/screenshots/pdf-source-final.png",
    fullPage: true,
  });
});
