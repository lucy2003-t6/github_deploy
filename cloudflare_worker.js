// Cloudflare Worker 保活脚本 / Keep-Alive Script
//
// === 部署步骤 / Deployment Steps ===
// 1. 登录 Cloudflare Dashboard -> 左侧菜单 "Workers & Pages"
// 2. 点击 "Create Application" -> "Create Worker"
// 3. 给它起个名字 (比如: render-keeper) -> 点击 "Deploy"
// 4. 部署成功后，点击 "Edit Code" (编辑代码)
// 5. **把这个文件的所有内容复制，覆盖掉 Cloudflare 编辑器里原来的代码**
// 6. 点击右上角 "Save and Deploy"
//
// === 设置定时 / Set Schedule ===
// 7. 回到 Worker 的详情页面 (点击左上角箭头返回)
// 8. 点击顶部的 "Triggers" (触发器) 标签
// 9. 找到 "Cron Triggers" (定时任务) -> 点击 "Add Cron Trigger"
// 10. 在 "Cron Expression" 里输入: */2 * * * *
//     (注意：是星号除以2，意思是每 2 分钟执行一次)
// 11. 点击 "Add"
//
// 完成！Cloudflare 现在会每 2 分钟帮您访问一次网站，确保它不休眠。

export default {
    // 定时任务入口 (Cron Trigger 会触发这个)
    async scheduled(event, env, ctx) {
        const url = "https://github-deploy-f5sj.onrender.com";
        console.log(`[Scheduled] Pinging ${url}...`);

        try {
            // 发送请求，不做任何处理，只是为了连接一下
            // Render 收到请求后就会重置休眠倒计时
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'User-Agent': 'Cloudflare-Worker-KeepAlive'
                }
            });
            console.log(`[Success] Status: ${response.status}`);
        } catch (error) {
            console.error(`[Error] Failed to ping: ${error}`);
        }
    },

    // HTTP 请求入口 (可选，方便您在浏览器里访问这个 Worker 来手动测试)
    async fetch(request, env, ctx) {
        const url = "https://github-deploy-f5sj.onrender.com";

        try {
            const start = Date.now();
            const response = await fetch(url);
            const duration = Date.now() - start;

            return new Response(`✅ 手动唤醒成功!\n目标: ${url}\n状态码: ${response.status}\n耗时: ${duration}ms`, {
                headers: { "content-type": "text/plain; charset=utf-8" },
            });
        } catch (err) {
            return new Response(`❌ 唤醒失败: ${err}`, { status: 500 });
        }
    },
};
