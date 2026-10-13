#!/usr/bin/env node
// push.js —— 本技能自进化流程的落地点：门禁 → 提交 → 推送 → 打 tag
//
// 用法：
//   node push.js "<说明>"     正常自进化提交（门禁不过会拒绝推送）
//   node push.js --check      只跑门禁，不碰 git（git 不可用时也能用）
//   node push.js --force      门禁红灯时强行提交（需显式给出，并在汇报里说明原因）
//   node push.js --no-tag     提交推送但不打 tag（默认每次都打）
//
// 设计依据：references/自进化与维护.md §六 位次决定推不推、§七 push / tag / 回滚纪律
//   1. 门禁前置：断链 / 负向声明 / 体量 / 版本号 / 脚本校验，任一红灯拒绝推送
//   2. 仓库根校验：C:/Users/... 与 D:/CToD/... 是同一目录的两个视图，必须 realpath 归一后比对
//   3. origin 校验：只允许推本技能自己的仓库
//   4. tag 是回滚的唯一落点，tag 名带 SKILL.md 的 version
//
// ⚠️ 必须用异步 execFile，不要改成 spawnSync：本机 spawnSync 一律 EBUSY（实测，
//    对 git / cmd / pwsh / 甚至不存在的可执行文件全部如此）。
//
// 退出码：0 成功 · 1 失败 · 2 门禁红灯（未 --force） · 3 仓库校验失败

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = __dirname;

const EXPECTED_ORIGIN = "git@github.com:steelan9199/autohotkey-v2-yashu.git";

const argv = process.argv.slice(2);
const FORCE = argv.includes("--force");
const CHECK_ONLY = argv.includes("--check");
const NO_TAG = argv.includes("--no-tag");
const message =
  argv.filter((a) => !a.startsWith("--"))[0] || `Update: ${new Date().toLocaleString("zh-CN")}`;

const norm = (p) => fs.realpathSync.native(p).replace(/\\/g, "/").toLowerCase();

async function git(args, options = {}) {
  const { stdout } = await execFileAsync("git", ["-C", SKILL_DIR, ...args], {
    encoding: "utf8",
    maxBuffer: 8 * 1024 * 1024,
    ...options,
  });
  return stdout.trim();
}

function readVersion() {
  const text = fs.readFileSync(path.join(SKILL_DIR, "SKILL.md"), "utf8");
  const fm = text.match(/^---\n([\s\S]*?)\n---/);
  const m = fm && fm[1].match(/^version:\s*(\S+)\s*$/m);
  if (!m) {
    console.error("❌ SKILL.md frontmatter 缺少 version 字段，先补上再推送。");
    process.exit(1);
  }
  return m[1];
}

function stamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

async function assertRepoRoot() {
  let top;
  try {
    top = await git(["rev-parse", "--show-toplevel"]);
  } catch (e) {
    console.error("❌ 当前目录不是 git 仓库：", e.message);
    process.exit(3);
  }
  let same = false;
  try {
    same = norm(top) === norm(SKILL_DIR);
  } catch {
    same = false;
  }
  if (!same) {
    console.error(`❌ 仓库根校验失败：git 认为仓库在 ${top}，技能目录是 ${SKILL_DIR}`);
    process.exit(3);
  }
  return top;
}

async function assertOrigin() {
  const remote = await git(["remote", "get-url", "origin"]);
  if (remote !== EXPECTED_ORIGIN) {
    console.error(`❌ origin 不是本技能仓库，拒绝推送。\n   期望：${EXPECTED_ORIGIN}\n   实际：${remote}`);
    process.exit(3);
  }
}

async function runAudit() {
  const auditPath = path.join(SKILL_DIR, "scripts", "skill_audit.js");
  try {
    const { stdout } = await execFileAsync(process.execPath, [auditPath], {
      encoding: "utf8",
      maxBuffer: 4 * 1024 * 1024,
    });
    console.log(stdout);
    return 0;
  } catch (e) {
    console.log((e.stdout || "") + (e.stderr || ""));
    return typeof e.code === "number" ? e.code : 1;
  }
}

async function main() {
  await assertRepoRoot();
  await assertOrigin();

  const auditCode = await runAudit();
  if (auditCode !== 0 && !FORCE) {
    console.error("\n❌ 门禁红灯，拒绝推送。先修干净，或显式加 --force（并在汇报里说明原因）。");
    process.exit(2);
  }
  if (auditCode !== 0 && FORCE) {
    console.warn("\n⚠️ 门禁红灯但 --force 生效，本次推送未过闸。");
  }
  if (CHECK_ONLY) {
    console.log("\n(--check 模式：门禁到此为止，未碰 git)");
    return;
  }

  if (!(await git(["status", "--porcelain"]))) {
    console.log("工作区干净，没有要提交的改动。");
    return;
  }

  const version = readVersion();
  await git(["add", "-A"]);
  await git(["commit", "-m", message]);
  const branch = (await git(["rev-parse", "--abbrev-ref", "HEAD"])) || "main";
  await git(["push", "origin", branch], { timeout: 180000 });
  console.log(`已推送分支：${branch}`);

  if (!NO_TAG) {
    const tag = `v${version}-${stamp()}`;
    await git(["tag", tag]);
    await git(["push", "origin", tag], { timeout: 180000 });
    console.log(`已打 tag：${tag}（回滚落点）`);
    console.log(`回滚文件：git -C "${SKILL_DIR}" checkout ${tag} -- .`);
  }

  console.log(`\n✅ 自进化落地：${message}`);
}

main().catch((e) => {
  console.error("❌ push.js 执行失败：", e.message || e);
  process.exit(1);
});
