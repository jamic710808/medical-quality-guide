'use strict';

// Run only after the main-line HTML is ready: node verify_guide.cjs [artifact-root]
// No browser or filesystem work occurs when this file is checked with node --check.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('C:/Users/jamic/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

const ROOT = path.resolve(process.argv[2] || 'C:/Users/jamic/.codex/visualizations/2026/10/31/01a18fc0-0876-7220-b07f-83c457684060/medical-triple-guide');
const HTML = '醫療病歷質控_三版影片互動導覽.html';
const MODES = ['motion', 'general', 'animation'];
const EXPECT = {
  motion: { chapters: 8, duration: 90, width: 1920, height: 1080 },
  general: { chapters: 12, duration: 137.15, width: 1280, height: 720 },
  animation: { chapters: 12, duration: 217.866667, width: 1280, height: 720 },
};
const MOTION_SYNC = [
  [0, 'dashboard'], [6, 'sources'], [18, 'rules'], [33, 'case'],
  [47, 'case'], [61, 'case'], [76, 'governance'], [86, 'release'],
];
const assert = (condition, message) => { if (!condition) throw new Error(message); };
const closeTo = (actual, expected, tolerance = 0.35) => Math.abs(actual - expected) <= tolerance;

(async () => {
  let context, page, profile, isolated;
  const errors = [], consoleErrors = [], external = [], failedRequests = [];
  const results = {
    status: 'running', source: path.join(ROOT, HTML), startedAt: new Date().toISOString(),
    checks: [], films: [], chapters: [], syncChecks: [], viewports: [], screenshots: [],
    browserErrors: errors, consoleErrors, externalRequests: external, failedRequests,
  };
  const check = async (name, action) => {
    try { await action(); results.checks.push({ name, passed: true }); }
    catch (error) { results.checks.push({ name, passed: false, error: error.message }); throw error; }
  };
  try {
    assert(fs.existsSync(results.source), `HTML not yet available: ${results.source}`);
    // A unique, empty directory prevents stale companion files from hiding dependencies.
    isolated = fs.mkdtempSync(path.join(ROOT, 'isolated-check-'));
    const file = path.join(isolated, HTML);
    fs.copyFileSync(results.source, file);
    const url = pathToFileURL(file).href;
    results.isolatedDirectory = isolated;
    results.isolatedFolderFiles = fs.readdirSync(isolated);
    assert(results.isolatedFolderFiles.length === 1, 'Isolation must contain exactly one HTML');

    profile = fs.mkdtempSync(path.join(os.tmpdir(), 'medical-triple-chrome-'));
    fs.writeFileSync(path.join(profile, 'Local State'), JSON.stringify({
      password_manager: {
        os_password_blank: false,
        os_password_last_changed: '9000000000000000000',
      },
    }));
    context = await chromium.launchPersistentContext(profile, {
      channel: 'chrome', headless: true, viewport: { width: 1440, height: 1000 },
      serviceWorkers: 'block',
    });
    context.setDefaultTimeout(15000);
    context.setDefaultNavigationTimeout(120000);
    context.on('page', p => p.on('pageerror', e => errors.push(e.message)));
    for (const p of context.pages()) p.on('pageerror', e => errors.push(e.message));
    context.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
    context.on('request', request => {
      const requested = request.url();
      if (!/^(blob:|data:|about:)/.test(requested) && requested.split('#')[0] !== url) external.push(requested);
    });
    context.on('requestfailed', request => failedRequests.push({ url: request.url(), error: request.failure()?.errorText }));
    await context.route(/^https?:\/\//, route => route.abort('blockedbyclient'));
    page = context.pages()[0] || await context.newPage();
    await page.goto(url, { waitUntil: 'load' });
    const video = page.locator('#ip-video');
    const filmButton = mode => page.locator(`[data-film="${mode}"]`);
    const pause = () => video.evaluate(v => { v.pause(); v.muted = true; });
    const ready = mode => page.waitForFunction(({ mode, duration }) => {
      const v = document.querySelector('#ip-video');
      return window.__introPack?.mode === mode && v?.readyState >= 2 &&
        !v.seeking && Math.abs(v.duration - duration) < 0.12;
    }, { mode, duration: EXPECT[mode].duration }, { timeout: 120000 });
    const select = async mode => { await pause(); await filmButton(mode).click(); await ready(mode); await pause(); };
    const seek = async seconds => {
      await pause();
      // Repeated endpoints still need a real native seek/timeupdate event.
      if (closeTo(await video.evaluate(v => v.currentTime), seconds, 0.01)) {
        const offset = seconds > 0.5 ? seconds - 0.4 : seconds + 0.4;
        await video.evaluate((v, t) => { v.currentTime = t; }, offset);
        await page.waitForFunction(t => !document.querySelector('#ip-video').seeking && Math.abs(document.querySelector('#ip-video').currentTime - t) < 0.1, offset);
      }
      await video.evaluate((v, t) => { v.currentTime = t; }, seconds);
      await page.waitForFunction(t => {
        const v = document.querySelector('#ip-video');
        return !v.seeking && Math.abs(v.currentTime - t) < 0.25;
      }, seconds);
      // Let timeupdate handlers and rendering complete without advancing playback.
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    };
    let contract;
    const activeKey = () => page.evaluate(() => {
      const p = window.__introPack;
      return typeof p.step === 'number' ? p.steps[p.step]?.key : p.step;
    });
    const waitStep = key => page.waitForFunction(key => {
      const p = window.__introPack;
      return (typeof p.step === 'number' ? p.steps[p.step]?.key : p.step) === key;
    }, key);
    const stepButton = index => page.locator(`[data-step="${index}"]`);

    await check('default motion, ordered tabs, public API and sync contract', async () => {
      assert(await page.evaluate(() => window.__introPack?.mode) === 'motion', 'Default must be motion');
      await ready('motion'); await pause();
      contract = await page.evaluate(() => {
        const p = window.__introPack;
        return { films: p.films, steps: p.steps, sync: p.sync,
          functions: ['setMode', 'seekTo'].map(k => typeof p[k]) };
      });
      assert(contract.functions.every(t => t === 'function'), 'Missing setMode/seekTo');
      const order = await page.locator('[data-film]').evaluateAll(nodes => nodes.map(n => n.dataset.film));
      assert(JSON.stringify(order) === JSON.stringify(MODES), `Film order: ${order}`);
      assert(contract.steps.length === 10, 'Expected 10 steps');
      const keys = contract.steps.map(s => s.key);
      assert(keys.every(k => typeof k === 'string') && new Set(keys).size === 10, 'Steps need unique string keys');
      for (const step of contract.steps) {
        assert(step.motionTime === null || (Number.isFinite(step.motionTime) && step.motionTime >= 0 && step.motionTime < 90), `Invalid motionTime: ${step.key}`);
      }
      for (const mode of MODES) {
        const sync = contract.sync?.[mode];
        assert(Array.isArray(sync) && sync.length > 0 && sync[0].start === 0, `Missing sync.${mode}`);
        sync.forEach((entry, i) => {
          assert(Number.isFinite(entry.start) && entry.start >= 0 && entry.start < EXPECT[mode].duration, `Invalid sync time: ${mode}/${i}`);
          assert(i === 0 || entry.start > sync[i - 1].start, `Unsorted sync: ${mode}/${i}`);
          assert(entry.step === null || keys.includes(entry.step), `Unknown sync step: ${mode}/${i}`);
        });
      }
      assert(JSON.stringify(contract.sync.motion.map(s => [s.start, s.step])) === JSON.stringify(MOTION_SYNC), 'Motion sync differs from required timeline');
      assert(!await page.locator('#ip-follow').isChecked(), 'Follow must be opt-in');
    });

    await check('three embedded videos, 32 chapter seeks and highlights, actual playback', async () => {
      await page.locator('#ip-follow').uncheck();
      for (const mode of MODES) {
        await select(mode);
        const expected = EXPECT[mode], chapters = contract.films[mode].chapters;
        assert(chapters.length === expected.chapters, `Declared chapter count: ${mode}`);
        assert(closeTo(contract.films[mode].duration, expected.duration, 0.12), `Declared duration: ${mode}`);
        assert(await page.locator('#ip-chapters button').count() === expected.chapters, `Rendered chapter count: ${mode}`);
        const meta = await video.evaluate(v => ({ duration: v.duration, width: v.videoWidth, height: v.videoHeight, src: v.currentSrc }));
        assert(/^(blob:|data:)/.test(meta.src), `Video must be embedded: ${mode}`);
        assert(closeTo(meta.duration, expected.duration, 0.12), `Video duration: ${mode}`);
        assert(meta.width === expected.width && meta.height === expected.height, `Video dimensions: ${mode}`);
        results.films.push({ mode, ...expected, actual: { ...meta, src: meta.src.split(':')[0] } });
        for (let i = 0; i < chapters.length; i++) {
          assert(Number.isFinite(chapters[i].start) && chapters[i].start >= 0 && chapters[i].start < meta.duration, `Chapter timestamp: ${mode}/${i}`);
          assert(i === 0 || chapters[i].start > chapters[i - 1].start, `Chapter order: ${mode}/${i}`);
          await page.locator('#ip-chapters button').nth(i).click(); await pause();
          await page.waitForFunction(t => Math.abs(document.querySelector('#ip-video').currentTime - t) < 0.5 && !document.querySelector('#ip-video').seeking, chapters[i].start);
          await page.waitForFunction(i => document.querySelectorAll('#ip-chapters button')[i]?.getAttribute('aria-current') === 'true', i);
          assert(await page.locator('#ip-chapters button[aria-current="true"]').count() === 1, 'Exactly one current chapter');
          results.chapters.push({ mode, index: i, start: chapters[i].start, passed: true });
        }
        await seek(1);
        await video.evaluate(v => v.play());
        await page.waitForFunction(() => document.querySelector('#ip-video').currentTime > 1.5);
        await pause();
      }
      assert(results.chapters.length === 32, 'Expected 32 chapter checks');
    });

    await check('independent per-film time memory and rapid switching recovery', async () => {
      const memory = { motion: 12.25, general: 42.25, animation: 82.25 };
      for (const mode of MODES) { await select(mode); await seek(memory[mode]); }
      for (const mode of ['motion', 'animation', 'general', 'motion']) {
        await select(mode);
        assert(closeTo(await video.evaluate(v => v.currentTime), memory[mode]), `Time memory: ${mode}`);
      }
      // Deliberately do not wait for media readiness between switches.
      await page.evaluate(() => {
        for (let i = 0; i < 30; i++) document.querySelector(`[data-film="${['motion', 'general', 'animation'][i % 3]}"]`).click();
        document.querySelector('[data-film="motion"]').click();
      });
      await ready('motion'); await pause();
      for (const mode of MODES) {
        await select(mode); await seek(2);
        await video.evaluate(v => v.play());
        await page.waitForFunction(() => document.querySelector('#ip-video').currentTime > 2.4);
        await pause();
      }
    });

    await check('three-tab keyboard wrap in both directions', async () => {
      await select('motion'); await filmButton('motion').focus();
      for (const [key, mode] of [
        ['ArrowRight', 'general'], ['ArrowRight', 'animation'], ['ArrowRight', 'motion'],
        ['ArrowLeft', 'animation'], ['ArrowLeft', 'general'], ['ArrowLeft', 'motion'],
      ]) {
        await page.keyboard.press(key); await ready(mode); await pause();
        assert(await filmButton(mode).evaluate(b => b === document.activeElement), `Keyboard focus: ${key}/${mode}`);
        assert(await filmButton(mode).getAttribute('aria-selected') === 'true', `Tab selection: ${mode}`);
      }
    });

    await check('10 screenshot steps, all hotspots, zoom and step keyboard navigation', async () => {
      for (let i = 0; i < 10; i++) {
        await stepButton(i).click(); await waitStep(contract.steps[i].key);
        await page.waitForFunction(() => { const im = document.querySelector('#ip-shot img'); return im?.complete && im.naturalWidth > 0; });
        const spots = page.locator('#ip-shot .hs'), count = await spots.count();
        assert(count > 0, `No hotspots: step ${i}`);
        for (let j = 0; j < count; j++) {
          await spots.nth(j).click();
          assert(await spots.nth(j).getAttribute('aria-pressed') === 'true', `Hotspot ${i}/${j}`);
          assert((await page.locator('#ip-shot .note span').innerText()).trim().length > 8, `Hotspot text ${i}/${j}`);
        }
        await page.locator('#ip-shot [data-zoom]').click();
        assert(await page.locator('#ip-lightbox').isVisible(), `Zoom opens: ${i}`);
        assert(await page.locator('#ip-lightbox img').evaluate(im => im.complete && im.naturalWidth > 0), `Zoom image: ${i}`);
        await page.locator('#ip-lbsize').click();
        assert(await page.locator('#ip-lightbox').evaluate(el => el.classList.contains('actual')), 'Original size toggle');
        await page.locator('#ip-lightbox').evaluate(el => { el.scrollTop = 100; el.scrollLeft = 100; });
        await page.keyboard.press('Escape');
        assert(!await page.locator('#ip-lightbox').isVisible(), 'Escape closes zoom');
      }
      await stepButton(8).focus(); await page.keyboard.press('Home'); await waitStep(contract.steps[0].key);
      assert(await stepButton(0).getAttribute('aria-selected') === 'true', 'Step Home');
    });

    await check('all step film bridges and disabled uncovered motion steps', async () => {
      let disabled = 0, enabled = 0;
      for (let i = 0; i < contract.steps.length; i++) {
        for (const mode of MODES) {
          await stepButton(i).click();
          const time = contract.steps[i][`${mode}Time`], button = page.locator(`#ip-watch-${mode}`);
          if (mode === 'motion' && time === null) {
            disabled++;
            assert(await button.isDisabled(), `Uncovered motion step enabled: ${i}`);
            const before = await page.evaluate(() => ({ mode: window.__introPack.mode, time: document.querySelector('#ip-video').currentTime }));
            await button.evaluate(b => b.click());
            const after = await page.evaluate(() => ({ mode: window.__introPack.mode, time: document.querySelector('#ip-video').currentTime }));
            assert(before.mode === after.mode && closeTo(before.time, after.time, 0.05), `Disabled bridge changed player: ${i}`);
          } else {
            assert(Number.isFinite(time), `Missing ${mode}Time: step ${i}`);
            assert(await button.isEnabled(), `Covered bridge disabled: ${mode}/${i}`);
            await button.click(); await ready(mode); await pause();
            assert(closeTo(await video.evaluate(v => v.currentTime), time, 0.75), `Bridge target: ${mode}/${i}`);
            if (mode === 'motion') enabled++;
          }
        }
      }
      assert(disabled > 0 && enabled > 0, 'Need covered and uncovered motion steps');
      results.motionBridges = { enabled, disabled };
    });

    await check('opt-in follow on/off and forward/reverse timeline seeking for every film', async () => {
      for (const mode of MODES) {
        await select(mode); await page.locator('#ip-follow').check();
        const sync = contract.sync[mode], chapters = contract.films[mode].chapters;
        // Every interval plus its exact starting boundary, visited in both directions.
        const points = [...new Set([...sync.flatMap((entry, i) => [entry.start,
          (entry.start + (sync[i + 1]?.start ?? EXPECT[mode].duration)) / 2]),
        ...chapters.map((entry, i) => (entry.start + (chapters[i + 1]?.start ?? EXPECT[mode].duration)) / 2)])].sort((a, b) => a - b);
        for (const direction of ['forward', 'reverse']) {
          for (const time of direction === 'forward' ? points : [...points].reverse()) {
            const mapped = [...sync].reverse().find(entry => entry.start <= time);
            if (mapped.step === null) {
              const sentinel = contract.steps[0].key;
              await stepButton(0).click(); await seek(time);
              assert(await activeKey() === sentinel, `Null sync should preserve manual step: ${mode}/${time}`);
            } else {
              // Force a different step so stale state cannot satisfy synchronization.
              await stepButton(contract.steps.findIndex(s => s.key !== mapped.step)).click();
              await seek(time); await waitStep(mapped.step);
            }
            const chapter = chapters.reduce((last, entry, i) => entry.start <= time ? i : last, 0);
            await page.waitForFunction(i => document.querySelectorAll('#ip-chapters button')[i]?.getAttribute('aria-current') === 'true', chapter);
            results.syncChecks.push({ mode, direction, time, step: mapped.step, chapter, passed: true });
          }
        }
        const transition = sync.find((entry, i) => i > 0 && entry.step !== null && entry.step !== sync[i - 1].step);
        assert(transition, `No testable playback-follow transition: ${mode}`);
        await seek(transition.start - 0.3);
        await video.evaluate(v => v.play());
        await page.waitForFunction(t => document.querySelector('#ip-video').currentTime > t + 0.15, transition.start);
        await waitStep(transition.step); await pause();
        await page.locator('#ip-follow').uncheck();
        await stepButton(0).click();
        for (const time of [EXPECT[mode].duration - 1, 0]) {
          await seek(time);
          assert(await activeKey() === contract.steps[0].key, `Follow-off changed step: ${mode}/${time}`);
        }
      }
    });

    await check('retained architecture and evidence interactions plus film bridge', async () => {
      await page.locator('[data-node="model"]').click();
      assert((await page.locator('#node-title').innerText()).includes('助手'), 'Architecture node content');
      await page.locator('#ip-arch-watch').click();
      const mode = await page.evaluate(() => window.__introPack.mode);
      assert(MODES.includes(mode), 'Architecture bridge selected unknown film');
      await ready(mode); await pause();
      assert(await video.evaluate(v => Number.isFinite(v.currentTime) && !v.error), 'Architecture bridge player');
      await page.locator('[data-case="missing"]').click();
      assert((await page.locator('#case-title').innerText()).includes('無法判斷'), 'Evidence interaction content');
    });

    await check('1440/390/360 responsive layout and desktop/mobile screenshots', async () => {
      await select('motion'); await stepButton(3).click();
      for (const width of [1440, 390, 360]) {
        await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
        const dims = await page.evaluate(() => ({ client: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth }));
        assert(dims.scroll <= dims.client + 1, `Page overflow at ${width}: ${JSON.stringify(dims)}`);
        assert(await page.locator('#ip-shot img').evaluate(im => im.complete && im.naturalWidth > 0), `Screenshot image at ${width}`);
        for (const mode of MODES) {
          await filmButton(mode).scrollIntoViewIfNeeded();
          const box = await filmButton(mode).boundingBox();
          assert(box && box.x >= -1 && box.x + box.width <= width + 1, `Tab outside viewport: ${width}/${mode}`);
          await select(mode);
          assert(await page.locator('#ip-chapters button').count() === EXPECT[mode].chapters, `Responsive chapters: ${mode}`);
        }
        await select('motion');
        for (const [label, selector] of [['video', '#video-demo'], ['tour', '#walkthrough']]) {
          const name = `${label}-${width}.png`;
          await page.locator(selector).screenshot({ path: path.join(ROOT, name), timeout: 30000 });
          results.screenshots.push(name);
        }
        results.viewports.push({ width, ...dims, bodyOverflow: false });
      }
    });

    await check('single-file dependency audit and zero JavaScript/console errors', async () => {
      const audit = await page.evaluate(() => {
        const refs = [...document.querySelectorAll('[src], [href], [poster], [srcset], [style], style')].flatMap(el => {
          const values = ['src', 'href', 'poster', 'srcset', 'style'].map(a => el.getAttribute(a)).filter(Boolean);
          if (el.tagName === 'STYLE') values.push(el.textContent);
          return values;
        });
        return { externalResources: performance.getEntriesByType('resource').map(r => r.name).filter(u => !/^(blob:|data:)/.test(u)),
          remoteReferences: refs.filter(value => /(?:https?:)?\/\//i.test(value.replace(/data:[^\s"']+/g, ''))),
          brokenImages: [...document.images].filter(im => !im.complete || im.naturalWidth === 0).map(im => im.id || im.alt) };
      });
      results.resourceAudit = audit;
      assert(external.length === 0, `External requests: ${JSON.stringify(external)}`);
      assert(audit.externalResources.length === 0, `Nonembedded resources: ${JSON.stringify(audit.externalResources)}`);
      assert(audit.brokenImages.length === 0, `Broken images: ${audit.brokenImages}`);
      assert(errors.length === 0, `JavaScript errors: ${JSON.stringify(errors)}`);
      assert(consoleErrors.length === 0, `Console errors: ${JSON.stringify(consoleErrors)}`);
      // Remote hyperlinks are reported, but navigation-only citations are not dependencies.
    });
    results.status = 'passed';
  } catch (error) {
    results.status = 'failed'; results.error = error.stack || String(error);
    process.exitCode = 1;
    if (page) {
      try { await page.screenshot({ path: path.join(ROOT, 'validation-failure.png') }); results.screenshots.push('validation-failure.png'); }
      catch (screenshotError) { results.failureScreenshotError = screenshotError.message; }
    }
  } finally {
    if (context) {
      try { await context.close(); }
      catch (error) { results.closeError = error.message; results.status = 'failed'; process.exitCode = 1; }
    }
    if (profile) {
      // Only this script's uniquely-created temporary Chrome profile is removed.
      try {
        const resolvedProfile = path.resolve(profile), relative = path.relative(path.resolve(os.tmpdir()), resolvedProfile);
        assert(relative && !relative.startsWith('..') && !path.isAbsolute(relative) && path.basename(resolvedProfile).startsWith('medical-triple-chrome-'), 'Unsafe profile cleanup path');
        fs.rmSync(resolvedProfile, { recursive: true, force: true, maxRetries: 3 });
      }
      catch (error) { results.profileCleanupError = error.message; }
    }
    if (errors.length || consoleErrors.length || external.length) { results.status = 'failed'; process.exitCode = 1; }
    results.finishedAt = new Date().toISOString();
    fs.writeFileSync(path.join(ROOT, 'browser-validation.json'), JSON.stringify(results, null, 2));
    console.log(JSON.stringify(results, null, 2));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
