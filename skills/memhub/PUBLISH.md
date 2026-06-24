# 发布说明：MemHub Skill

## 建议发布信息

- Slug: `memhub`
- Display name: `MemHub`
- Version: `0.4.2`
- Tags: `memory`, `memhub`, `github`, `gitee`, `sync`, `agent-memory`
- Summary: `跨 Agent 统一记忆仓库 Skill：直写/检索/遗忘记忆，按小时节流的自动 Git 同步，GitHub/Gitee OAuth 开箱即用（内置 Auth Broker），doctor 自检，多设备结构化合并。`
- Changelog: `GitHub/Gitee OAuth 统一走内置 MemHub Auth Broker（v2 session 协议），开箱即用、无需任何环境变量；doctor 增加 broker 就绪检查；保留 token/SSH/直连 fallback。`

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
  -F 'payload={"slug":"memhub","displayName":"MemHub","version":"0.4.1","changelog":"remember 默认直写 canonical；新增 search/forget/doctor；节流自动同步；结构化 merge 驱动多设备自动合并。","tags":["memory","memhub","github","gitee","sync","agent-memory"],"acceptLicenseTerms":true}' \
  -F 'files=@SKILL.md;type=text/markdown' \
  -F 'files=@README.md;type=text/markdown' \
  -F 'files=@scripts/memhub.py;type=text/plain' \
  -F 'files=@templates/context-pack.md.j2;type=text/plain'
```

两个易踩的坑（OpenAPI 文档未写明，但服务端强制）：

- **必须带 `"acceptLicenseTerms":true`**（放在 payload JSON 里），否则报
  `MIT-0 license terms must be accepted to publish skills`。
- **每个文件必须显式声明文本 MIME 类型**（`;type=text/plain` 或 `text/markdown`）。
  curl 默认把 `.py`/`.j2` 当 `application/octet-stream`，会被
  `Only text-based files are allowed` 拒绝。

成功返回 `{"ok":true,"skillId":...,"versionId":...}`。同一 slug 递增 `version`
即发布新版本（无单独的更新接口）。
