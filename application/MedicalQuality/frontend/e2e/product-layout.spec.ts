import { test, expect, type Page } from "@playwright/test";

test.setTimeout(30000);

async function login(page: Page, actor = "qc1") {
  await page.goto("/");
  await page.getByRole("combobox").selectOption(actor);
  await page.getByRole("button", { name: "進入工作區", exact: true }).click();
  await expect(page.locator(".mq-shell")).toBeVisible();
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 1280, height: 800 },
  { width: 1280, height: 720 },
]) {
  test(`工作臺滾動到底仍有分頁和外部留白 ${viewport.width}x${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await login(page);
    await expect(page.locator(".case-list tbody tr").first()).toBeVisible();
    const region = page.locator(".case-list .table-scroll");
    await region.evaluate((element) => {
      element.scrollTop = element.scrollHeight;
    });
    const box = await page.locator(".case-list").boundingBox();
    expect(viewport.height - box!.y - box!.height).toBeGreaterThanOrEqual(23);
    await expect(
      page.getByRole("button", { name: "下一頁", exact: true }),
    ).toBeInViewport();
    await expect(page.locator(".case-list tbody tr").last()).toBeInViewport();
    const doc = await page.evaluate(() => ({
      width: document.documentElement.scrollWidth,
      height: document.documentElement.scrollHeight,
    }));
    expect(doc).toEqual(viewport);
    const next = page.getByRole("button", { name: "下一頁", exact: true });
    await next.click();
    await expect(page).toHaveURL(/page=2/);
    await expect(page.locator(".case-list .pagination")).toContainText("第 9");
    await page.screenshot({
      path: `../artifacts/verification/screenshots/product-workbench-final-${viewport.width}-${viewport.height}.png`,
    });
  });
}

test("搜索無結果可復原，第二頁返回保留滾動位置", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await login(page);
  await page
    .getByRole("textbox", { name: "搜索病例" })
    .fill("不會存在的病例編號-zxq");
  await page.getByRole("button", { name: "搜索", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "沒有符合篩選條件的病例" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "清除篩選，查看全部", exact: true })
    .click();
  await expect(page.locator(".case-list tbody tr")).toHaveCount(8);
  await page.getByRole("button", { name: "下一頁", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
  const list = page.locator(".case-list .table-scroll");
  await list.evaluate((el) => (el.scrollTop = el.scrollHeight));
  await page
    .getByRole("button", { name: "打開病例 陳**" })
    .scrollIntoViewIfNeeded();
  const position = await list.evaluate((el) => el.scrollTop);
  await page.getByRole("button", { name: "打開病例 陳**" }).click();
  await expect(
    page.getByRole("heading", { name: "陳**的病歷質控" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "返回病例隊列", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
  await expect.poll(() => list.evaluate((el) => el.scrollTop)).toBe(position);
});

test("當前問題和頁簽在刷新及圖譜往返後保持", async ({ page }) => {
  await login(page);
  await page.goto("/cases/C008?return=%2F%3Fpage%3D2");
  const item = page.locator(".finding-item").last();
  await item.click();
  const expected = await item.locator("strong").textContent();
  const task = new URL(page.url()).searchParams.get("task");
  await page.reload();
  await expect(page.locator(".finding-item.selected strong")).toHaveText(
    expected!,
  );
  await page.getByRole("button", { name: "查看證據關係", exact: true }).click();
  await expect(page.getByTestId("ontology-graph-canvas")).toBeVisible();
  await page.getByRole("button", { name: "返回原任務", exact: true }).click();
  expect(new URL(page.url()).searchParams.get("task")).toBe(task);
  await expect(page.locator(".finding-item.selected strong")).toHaveText(
    expected!,
  );
  await page.getByRole("button", { name: "操作記錄", exact: true }).click();
  await page.reload();
  await expect(
    page.getByRole("button", { name: "操作記錄", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
});

test("資料分頁與長彈窗可用，關閉後接續原頁", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await login(page);
  await page.getByRole("link", { name: "資料接入", exact: true }).click();
  await expect(page.locator(".source-list tbody tr")).toHaveCount(8);
  await page.getByRole("button", { name: "下一頁", exact: true }).click();
  await expect(page.locator(".source-list .pagination")).toContainText("第 9");
  await page.getByRole("button", { name: "查看", exact: true }).first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page
    .getByRole("button", { name: "查看解析證據與病例接入", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "當前來源沒有可瀏覽的解析結果" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "返回資料目錄", exact: true }).click();
  await expect(page.locator(".source-list .pagination")).toContainText("第 9");
  await page.getByRole("textbox", { name: "篩選資料名稱" }).fill("病案首頁");
  await expect(page.locator(".source-list tbody tr")).toHaveCount(1);
  await expect(page.locator(".source-list .pagination")).toContainText(
    "共 1 條",
  );
  await page.getByRole("button", { name: "查看", exact: true }).click();
  await page
    .getByRole("button", { name: "查看解析證據與病例接入", exact: true })
    .click();
  await expect(page.locator(".source-record").first()).toBeVisible();
  await page
    .locator(".modal-body")
    .evaluate((el) => (el.scrollTop = el.scrollHeight));
  await expect(
    page.getByRole("button", { name: "關閉", exact: true }),
  ).toBeInViewport();
  await expect
    .poll(async () => {
      const box = await page.getByRole("dialog").boundingBox();
      return Math.min(box!.y, 800 - box!.y - box!.height);
    })
    .toBeGreaterThanOrEqual(31);
  expect(
    await page.locator(".mq-shell").evaluate((el) => (el as HTMLElement).inert),
  ).toBe(true);
  await page.screenshot({
    path: "../artifacts/verification/screenshots/product-modal-final-1280-800.png",
  });
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByRole("textbox", { name: "篩選資料名稱" })).toHaveValue(
    "病案首頁",
  );
  const returnPath = new URL(page.url()).pathname + new URL(page.url()).search;
  await page.reload();
  await expect(page.getByRole("textbox", { name: "篩選資料名稱" })).toHaveValue(
    "病案首頁",
  );
  await page.goto("/cases/C001?return=" + encodeURIComponent(returnPath));
  await page.getByRole("button", { name: "返回資料目錄", exact: true }).click();
  await expect(page.getByRole("textbox", { name: "篩選資料名稱" })).toHaveValue(
    "病案首頁",
  );
  await expect(page.locator(".source-list .pagination")).toContainText(
    "共 1 條",
  );
});

test("圖譜設計器與長管理頁保持底部空間", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await login(page);
  await page.getByRole("link", { name: "知識圖譜" }).click();
  await expect(page.getByTestId("ontology-graph-canvas")).toBeVisible();
  await page.getByRole("button", { name: "設計本體", exact: true }).click();
  await expect(page.locator(".designer-page")).toBeVisible();
  const graph = await page.locator(".native-workspace").boundingBox();
  expect(800 - graph!.y - graph!.height).toBeGreaterThanOrEqual(23);
  await expect(
    page.getByRole("button", { name: "保存候選", exact: true }),
  ).toBeInViewport();
  await page.screenshot({
    path: "../artifacts/verification/screenshots/product-designer-final-1280-800.png",
  });
  await page.getByRole("link", { name: "權限與審計", exact: true }).click();
  await expect(page.locator(".data-table tbody tr").first()).toBeVisible();
  await page
    .locator(".page-scroll")
    .evaluate((el) => (el.scrollTop = el.scrollHeight));
  const content = await page.locator(".page-scroll").boundingBox();
  expect(800 - content!.y - content!.height).toBeGreaterThanOrEqual(23);
  await expect(
    page.getByRole("button", { name: "下一頁", exact: true }),
  ).toBeInViewport();
  expect(await page.evaluate(() => document.documentElement.scrollHeight)).toBe(
    800,
  );
});
