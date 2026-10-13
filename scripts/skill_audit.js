#!/usr/bin/env node
// skill_audit.js —— 本技能的自进化门禁（改完必跑）
//
// 用法：
//   node scripts/skill_audit.js          跑门禁，打印结果
//   node scripts/skill_audit.js --top    附体量明细
//   node scripts/skill_audit.js --json   机器可读
// 退出码：0 = 全绿；1 = 有红灯
//
// 五道闸（任一红灯即失败）：
//   1. 引用断链  —— SKILL.md / references 里提到的文件是否存在
//   2. 负向声明  —— 全库有无「已废弃 / 勿再使用 / 已推翻 / 曾要求」类痕迹
//   3. 体量红线  —— SKILL.md ≤10000 字符、每篇 references/*.md ≤30000 字符
//   4. version   —— frontmatter 必须有 version 且为语义化版本
//   5. 脚本可跑  —— scripts/ 下所有 .ahk 必须过 ahk_check.py --strict
// 设计依据：references/自进化与维护.md §八 复测
//
// ⚠️ 本文件必须用异步 child_process（execFile），不要改成 spawnSync：
//    实测本机 spawnSync 对任何可执行文件都返回 EBUSY，见 §七 push / tag / 回滚纪律。

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.resolve(__dirname, "..");

const PYTHON = "D:/software/uv/python/cpython-3.14.7-windows-x86_64-none/python.exe";
const BUDGET = { "SKILL.md": 10000, reference: 30000 };

const NEGATIVE_PATTERNS = [/已废弃/, /勿再使用/, /已推翻/, /曾要求/];
// 禁令的载体必须能引述被禁的词形，故这两处豁免
const NEGATIVE_EXEMPT = ["自进化与维护.md", "skill_audit.js"];

const FILE_REF = /`([A-Za-z0-9_./\u4e00-\u9fa5*-]+\.(?:md|js|py|ahk))`/g;

function charCount(text) {
  return [...text].length;
}

function listDocs() {
  const docs = [path.join(SKILL_DIR, "SKILL.md")];
  const refDir = path.join(SKILL_DIR, "references");
  if (fs.existsSync(refDir)) {
    for (const f of fs.readdirSync(refDir)) {
      if (f.endsWith(".md")) docs.push(path.join(refDir, f));
    }
  }
  return docs;
}

function listAhkFiles(dir = path.join(SKILL_DIR, "scripts"), acc = []) {
  if (!fs.existsSync(dir)) return acc;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) listAhkFiles(full, acc);
    else if (entry.name.endsWith(".ahk")) acc.push(full);
  }
  return acc;
}

function resolveRef(ref) {
  if (/^[A-Za-z]:/.test(ref) || ref.startsWith("\\\\")) return null; // 绝对路径不管
  const clean = ref.replace(/^\.\//, "");
  const known = clean.startsWith("scripts/") || clean.startsWith("references/") || clean === "SKILL.md";
  if (!known) return null;
  const target = path.join(SKILL_DIR, clean);
  if (clean.includes("*")) {
    const dir = path.dirname(target);
    const ext = path.extname(clean);
    if (!fs.existsSync(dir)) return ref;
    return fs.readdirSync(dir).some((f) => f.endsWith(ext)) ? null : ref;
  }
  return fs.existsSync(target) ? null : ref;
}

function checkDocs() {
  const brokenRefs = [];
  const negatives = [];
  const oversize = [];
  const sizes = [];
  let version = null;
  let versionProblem = null;

  for (const file of listDocs()) {
    const base = path.basename(file);
    const text = fs.readFileSync(file, "utf8");
    const chars = charCount(text);
    const limit = base === "SKILL.md" ? BUDGET["SKILL.md"] : BUDGET.reference;
    sizes.push({ file: path.relative(SKILL_DIR, file), chars, limit });
    if (chars > limit) {
      oversize.push(`${path.relative(SKILL_DIR, file)}：${chars} > ${limit} 字符，必须拆分`);
    }

    for (const m of text.matchAll(FILE_REF)) {
      const missing = resolveRef(m[1]);
      if (missing) brokenRefs.push(`${path.relative(SKILL_DIR, file)} → ${missing}`);
    }

    if (!NEGATIVE_EXEMPT.includes(base)) {
      text.split("\n").forEach((line, i) => {
        if (NEGATIVE_PATTERNS.some((re) => re.test(line))) {
          negatives.push(`${path.relative(SKILL_DIR, file)}:${i + 1}  ${line.trim().slice(0, 70)}`);
        }
      });
    }

    if (base === "SKILL.md") {
      const fm = text.match(/^---\n([\s\S]*?)\n---/);
      const m = fm && fm[1].match(/^version:\s*(\S+)\s*$/m);
      if (!m) versionProblem = "SKILL.md frontmatter 缺少 version 字段";
      else if (!/^\d+\.\d+\.\d+$/.test(m[1])) versionProblem = `version 不是语义化版本：${m[1]}`;
      else version = m[1];
    }
  }

  return { brokenRefs, negatives, oversize, sizes, version, versionProblem };
}

async function checkAhkScripts() {
  const files = listAhkFiles();
  const failures = [];
  for (const file of files) {
    const rel = path.relative(SKILL_DIR, file);
    try {
      const { stdout } = await execFileAsync(PYTHON, [
        path.join(SKILL_DIR, "scripts", "ahk_check.py"), file, "--strict",
      ], { encoding: "utf8", maxBuffer: 4 * 1024 * 1024 });
      if (!stdout.includes("✅ 通过")) failures.push(`${rel}：未通过 --strict`);
    } catch (err) {
      const out = (err.stdout || "") + (err.stderr || "");
      const first = out.split("\n").find((l) => l.includes("❌")) || "校验失败";
      failures.push(`${rel}：${first.trim()}`);
    }
  }
  return { count: files.length, failures };
}

async function main() {
  const asJson = process.argv.includes("--json");
  const showTop = process.argv.includes("--top");

  const docs = checkDocs();
  const ahk = await checkAhkScripts();

  const reds = [];
  if (docs.brokenRefs.length) reds.push(`引用断链 ${docs.brokenRefs.length} 处`);
  if (docs.negatives.length) reds.push(`负向声明 ${docs.negatives.length} 处`);
  if (docs.oversize.length) reds.push(`体量超限 ${docs.oversize.length} 篇`);
  if (docs.versionProblem) reds.push(`版本号：${docs.versionProblem}`);
  if (ahk.failures.length) reds.push(`脚本校验未过 ${ahk.failures.length} 个`);

  if (asJson) {
    console.log(JSON.stringify({ version: docs.version, reds, ...docs, ahk }, null, 2));
    return reds.length ? 1 : 0;
  }

  console.log(`技能版本：${docs.version ?? "（缺失）"}`);
  console.log(`脚本校验：${ahk.count} 个 .ahk`);
  if (showTop) {
    console.log("\n体量：");
    for (const s of docs.sizes.sort((a, b) => b.chars - a.chars)) {
      const pct = ((s.chars / s.limit) * 100).toFixed(0);
      console.log(`  ${s.chars.toString().padStart(6)} / ${s.limit}  (${pct}%)  ${s.file}`);
    }
  }

  const sections = [
    ["引用断链", docs.brokenRefs],
    ["负向声明", docs.negatives],
    ["体量超限", docs.oversize],
    ["脚本校验", ahk.failures],
    ["版本号", docs.versionProblem ? [docs.versionProblem] : []],
  ];
  let printed = false;
  for (const [title, items] of sections) {
    if (!items.length) continue;
    printed = true;
    console.log(`\n❌ ${title}：`);
    for (const it of items) console.log(`   ${it}`);
  }

  if (reds.length) {
    console.log(`\n❌ 门禁红灯 ${reds.length} 类：${reds.join("；")}`);
    return 1;
  }
  console.log("\n✅ 通过：断链、负向声明、体量、版本号、脚本校验全部干净。");
  return 0;
}

main().then((code) => process.exit(code)).catch((e) => {
  console.error("门禁自身出错：", e);
  process.exit(1);
});
