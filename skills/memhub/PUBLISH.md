# 发布说明：MemHub Skill

## 建议发布信息

- Slug: `memhub`
- Display name: `MemHub`
- Version: `0.4.4`
- Tags: `memory`, `memhub`, `github`, `gitee`, `sync`, `agent-memory`
- Summary: `跨 Agent 统一记忆仓库 Skill：onboard 一键首次接入（拉取已有记忆或建仓），直写/检索/遗忘，节流自动同步，GitHub/Gitee OAuth 开箱即用（内置 Auth Broker），doctor 自检，多设备结构化合并。`
- Changelog: `修复发布包结构：保留 scripts/ 与 templates/ 子目录前缀，使其与 SKILL.md 中 python scripts/memhub.py 的引用一致（此前被压成扁平结构，安装后脚本路径找不到）。`

## 包内容

发布包应只包含：

```text
SKILL.md
README.md
scripts/memhub.py
templates/context-pack.md.j2
```

不得包含：

```text
__pycache__/
*.pyc
.git/
.memhub/secrets.yaml
用户个人记忆数据
真实 token / client secret / authorization code
```

## SkillHub.cn 上架流程

1. 打开 `https://skillhub.cn/`。
2. 登录账号。
3. 进入个人中心或点击「发布 Skill」。
4. 如提示实名认证/团队认证，先按平台要求完成。
5. 上传发布包 zip 或文件夹。
6. 填写 Slug、名称、版本、简介、变更说明和标签。
7. 提交并等待安全扫描/审核。

SkillHub Web 端发布接口需要登录态 cookie，当前仓库不保存也不应保存该凭据，因此不能在无登录态环境中代提交。

## ClawHub.ai 上架流程

ClawHub 支持网页上传，也提供 OpenAPI：`https://clawhub.ai/api/v1/openapi.json`。

网页方式：

1. 打开 `https://clawhub.ai/`。
2. 登录账号。
3. 进入发布 Skill 页面。
4. 上传发布包 zip 或文件夹。
5. 填写 Slug、名称、版本、简介、变更说明和标签。
6. 提交。

API 方式需要 Bearer API token。请在安全环境里设置环境变量，不要把 token 写进仓库或聊天记录：

```bash
curl -X POST https://clawhub.ai/api/v1/skills \
  -H "Authorization: Bearer $CLAWHUB_TOKEN" \
  -F 'payload={"slug":"memhub","displayName":"MemHub","version":"0.4.3","changelog":"...","tags":["memory","memhub","github","gitee","sync","agent-memory"],"acceptLicenseTerms":true}' \
  -F 'files=@SKILL.md;filename=SKILL.md;type=text/markdown' \
  -F 'files=@README.md;filename=README.md;type=text/markdown' \
  -F 'files=@scripts/memhub.py;filename=scripts/memhub.py;type=text/plain' \
  -F 'files=@templates/context-pack.md.j2;filename=templates/context-pack.md.j2;type=text/plain'
```

三个易踩的坑（OpenAPI 文档未写明，但服务端强制 / 实测得出）：

- **必须带 `"acceptLicenseTerms":true`**（放在 payload JSON 里），否则报
  `MIT-0 license terms must be accepted to publish skills`。
- **每个文件必须显式声明文本 MIME 类型**（`;type=text/plain` 或 `text/markdown`）。
  curl 默认把 `.py`/`.j2` 当 `application/octet-stream`，会被
  `Only text-based files are allowed` 拒绝。
- **必须用 `filename=` 显式带上子目录前缀**（`filename=scripts/memhub.py`）。
  curl 的 `@path` 默认只发 basename，会把包压成扁平结构（`memhub.py` 而非
  `scripts/memhub.py`），与 SKILL.md 里 `python scripts/memhub.py` 的引用对不上，
  安装后 agent 找不到脚本。ClawHub 已验证支持带斜杠的 path。

成功返回 `{"ok":true,"skillId":...,"versionId":...}`。同一 slug 递增 `version`
即发布新版本（无单独的更新接口）。可用 `DELETE /api/v1/skills/{slug}` 删除（会保留
slug 一段时间）。
