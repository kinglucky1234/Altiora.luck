// Altiora 前端主逻辑
const API = window.location.origin;

// ─── 状态 ───
let state = {
    data: null,          // 后端返回的全部数据
    selected_option: {},  // 每个冲突选了哪个 option
    avatar_emoji: "🧑‍💻",
    profile: null,
};

// ─── Tab 切换 ───
document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    });
});

// ─── 初始化（先拿 mock 数据，让页面先跑起来） ───
async function init() {
    const res = await fetch(`${API}/api/mock`);
    state.data = await res.json();
    state.profile = state.data.profile;
    state.avatar_emoji = state.profile?.emoji || "🧑‍💻";

    renderGazeBar();
    renderGantt();
    renderAvatar();
    renderConflictCards();
    renderProfile();
    setupCloneForm();
    setupChat();
}

// ─── 顶部凝视条 ───
function renderGazeBar() {
    const d = state.data;
    document.getElementById("gaze-progress").textContent = "偏差 -15%";
    const statusEl = document.getElementById("gaze-status");
    if (d.total_conflicts > 0) {
        statusEl.textContent = `● 今日 ${d.total_conflicts} 处冲突`;
        statusEl.classList.add("warn");
    } else {
        statusEl.textContent = "● 今日无冲突 ✓";
    }
}

// ─── 甘特图 ───
function renderGantt() {
    document.getElementById("gantt-date").textContent = new Date().toLocaleDateString("zh-CN", { weekday: "long" });

    const chart = echarts.init(document.getElementById("gantt-chart"), "dark");
    const gantt = state.data.gantt;

    // 时间轴：6:00 - 24:00
    const startHour = 6;
    const endHour = 24;
    const totalMinutes = (endHour - startHour) * 60;

    // 配色
    const type_color = {
        class: "#60a5fa", work: "#f59e0b", meeting: "#a78bfa",
        study: "#34d399, commute: "#94a3b8", sleep: "#64748b", other: "#94a3b8",
    };

    // 生成 ECharts timeline data
    const names = [...new Set(gantt.map(e => e.name))];
    const rows = names.map(name => ({
        name,
        data: gantt
            .filter(e => e.name === name)
            .map(e => ({
                value: [
                    name,
                    (e.start_min - startHour * 60) / totalMinutes * 100,   // left %
                    (e.end_min - e.start_min) / totalMinutes * 100,        // width %
                    e,
                ],
            })),
    }));

    const option = {
        backgroundColor: "transparent",
        grid: { left: 80, right: 20, top: 10, bottom: 30 },
        xAxis: {
            type: "value", min: 0, max: 100,
            axisLabel: {
                formatter: v => `${Math.round(v / 100 * totalMinutes / 60) + startHour}:00`,
                color: "#8b8d93",
            },
            splitLine: { lineStyle: { color: "#1f2128" } },
        },
        yAxis: {
            type: "category",
            data: names,
            axisLabel: { color: "#8b8d93" },
            axisLine: { show: false },
            axisTick: { show: false },
        },
        series: rows.map(row => ({
            type: "custom",
            name: row.name,
            renderItem: (params, api) => {
                const item = api.value(3);
                const is_conflict = item.conflict;
                const color = type_color[item.type] || "#94a3b8";

                const x = api.coord([api.value(1), params.value]);
                const width = api.size([api.value(2), 0])[0];
                const y = api.coord([0, params.value]);
                const height = api.size([0, 1])[1] * 0.6;

                return {
                    type: "rect",
                    shape: { x, y: y - height / 2, width, height, r: 4 },
                    style: {
                        fill: is_conflict ? "#ef4444" : color,
                        shadowBlur: is_conflict ? 12 : 0,
                        shadowColor: "#ef4444",
                    },
                };
            },
            encode: { x: [1, 2], y: 0 },
            data: row.data,
        })),
    };

    chart.setOption(option);
    window.addEventListener("resize", () => chart.resize());
}

// ─── 分身 ───
function renderAvatar() {
    document.getElementById("avatar").textContent = state.avatar_emoji;
    const status = state.data.total_conflicts > 0 ? "warn" : "";
    document.getElementById("avatar-status").textContent =
        state.data.total_conflicts > 0
            ? `今天 ${state.data.total_conflicts} 处冲突 · 完成率 60%`
            : "今天无冲突 · 状态良好";
    const halo = document.getElementById("avatar-halo");
    halo.className = `halo ${status ? "halo-red" : "halo-green"}`;

    // 光带也跟着变
    const bar = document.getElementById("light-bar");
    bar.className = "light-bar " + (status ? "warn" : "");
}

// ─── 冲突卡片 ───
function renderConflictCards() {
    const container = document.getElementById("conflict-container");
    const cards = state.data.conflict_cards;

    if (!cards || cards.length === 0) {
        container.innerHTML = `<div style="text-align:center;color:#8b8d93;padding:20px;">今天没有冲突 ✓</div>`;
        return;
    }

    container.innerHTML = cards.map(card => `
        <div class="conflict-card">
            <div class="conflict-title">🔴 冲突</div>
            ${card.cards.map(opt => `
                <div class="option" data-conflict="${card.conflict_id}" data-choice="${opt.choice}">
                    <div class="option-choice">${opt.emoji} 选项${opt.choice}${opt.shift_to ? `（挪到 ${opt.shift_to}）` : ""}</div>
                    <ul class="option-gains">${opt.gains.map(g => `<li>📈 ${g}</li>`).join("")}</ul>
                    <ul class="option-costs">${opt.costs.map(c => `<li>📉 ${c}</li>`).join("")}</ul>
                </div>
            `).join("")}
            <div class="suggestion">
                <span class="suggestion-label">Altiora 建议：</span>${card.suggestion}
            </div>
        </div>
    `).join("");

    // 点击选选项
    container.querySelectorAll(".option").forEach(el => {
        el.addEventListener("click", () => {
            const conflict = el.dataset.conflict;
            const choice = el.dataset.choice;
            container.querySelectorAll(`.option[data-conflict="${conflict}"]`).forEach(o => o.classList.remove("selected"));
            el.classList.add("selected");
            state.selected_option[conflict] = choice;
            console.log("Selected:", conflict, choice);
        });
    });
}

// ─── 画像 Tab ───
function renderProfile() {
    const p = state.data.profile;
    document.getElementById("profile-display").innerHTML = `
        <div class="profile-item">
            <div class="profile-label">名字</div>
            <div class="profile-value">${p.name || "同学"}</div>
        </div>
        <div class="profile-item">
            <div class="profile-label">硬约束</div>
            <div class="profile-value">睡觉不晚于 ${p.hard_sleep_deadline}</div>
        </div>
        <div class="profile-item">
            <div class="profile-label">精力最好时段</div>
            <div class="profile-value">${p.preferred_focus_hours}</div>
        </div>
        <div class="profile-item">
            <div class="profile-label">已知弱点</div>
            <div class="profile-value">${p.known_weakness.join("、") || "未填写"}</div>
        </div>
        <div class="profile-item">
            <div class="profile-label">长期目标</div>
            <div class="profile-value">${p.long_term_goal || "未填写"}</div>
        </div>
        <div class="profile-item">
            <div class="profile-label">分身 emoji</div>
            <div class="profile-value">${state.avatar_emoji}</div>
        </div>
    `;
}

// ─── Clone Form ───
function setupCloneForm() {
    // emoji 选择
    document.querySelectorAll(".emoji-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".emoji-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            state.avatar_emoji = btn.textContent;
        });
    });

    document.getElementById("clone-form").addEventListener("submit", e => {
        e.preventDefault();
        // 暂时存到 state 和 localStorage，后端后续加
        const profile = {
            name: document.getElementById("clone-name").value || "同学",
            hard_sleep_deadline: document.getElementById("clone-sleep").value,
            preferred_focus_hours: document.getElementById("clone-focus").value,
            known_weakness: document.getElementById("clone-weakness").value.split("\n").filter(x => x.trim()),
            long_term_goal: document.getElementById("clone-goal").value,
        };
        state.profile = { ...state.data.profile, ...profile, emoji: state.avatar_emoji };
        localStorage.setItem("altiora_profile", JSON.stringify(state.profile));
        alert("Altiora 已生成！切换到 Plan tab 看效果。");
        renderProfile();
    });

    // 恢复上次保存的 profile
    const saved = localStorage.getItem("altiora_profile");
    if (saved) {
        try {
            state.profile = JSON.parse(saved);
            state.avatar_emoji = state.profile.emoji || state.avatar_emoji;
        } catch {}
    }
}

// ─── Chat ───
function setupChat() {
    const input = document.getElementById("chat-input");
    const send = document.getElementById("chat-send");
    const messages = document.getElementById("chat-messages");

    function addMsg(text, isUser) {
        const div = document.createElement("div");
        div.className = isUser ? "msg-user" : "msg-altiora";
        div.textContent = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    // 欢迎消息
    addMsg("我是 Altiora。粘课表、吐槽状态、说你的目标——你说什么都行。", false);

    send.addEventListener("click", sendChat);
    input.addEventListener("keydown", e => e.key === "Enter" && sendChat());

    async function sendChat() {
        const text = input.value.trim();
        if (!text) return;
        input.value = "";
        addMsg(text, true);

        // 简单 Mock：看看用户粘的是不是课表（有时间格式）
        const looks_like_course = /\d{1,2}:\d{2}/.test(text);

        if (looks_like_course) {
            addMsg("我读到了课表，正在解析...（Mock 模式：直接用示例日程）", false);
        } else if (text.includes("累") || text.includes("状态")) {
            addMsg("收到。你的状态我记下来了——明天规划时我会考虑。", false);
        } else if (text.includes("目标") || text.includes("想")) {
            addMsg("好，我把你的目标存进画像卡里了。下次规划会参考。", false);
        } else {
            addMsg("嗯，我听到了。你可以说具体点——比如粘课表、说今天状态、或者讲你的长期目标。", false);
        }
    }
}

// ─── 启动 ───
init();
