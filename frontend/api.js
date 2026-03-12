/**
 * EmoHealer 前端API服务
 * 使用Mock数据模拟后端接口，便于前端开发调试
 * 
 * 使用方式：
 * 1. 开发时：引入本文件，使用 MockAPI.xxx() 调用
 * 2. 上线时：将 BASE_URL 改为实际后端地址
 */

// ==================== 配置 ====================
const BASE_URL = 'http://localhost:8090/api';
const USE_MOCK = false; // 连接真实后端API

// ==================== Mock数据 ====================
const MockData = {
    // 用户数据
    users: [
        { id: 1, username: 'zhangsan', nickname: '阳光少年', avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan', role: 'user' },
        { id: 2, username: 'lisi', nickname: '温暖女孩', avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=lisi', role: 'user' }
    ],

    // 用户信息
    userInfo: {
        id: 1,
        username: 'zhangsan',
        nickname: '阳光少年',
        avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan',
        email: 'zhangsan@example.com',
        role: 'user',
        created_at: '2026-03-01T10:00:00'
    },

    // 对话历史
    chatHistory: [
        { id: 1, user_message: '我今天心情不好', ai_reply: '我在这里倾听你。慢慢说，不要着急。', emotion_type: 'sad', created_at: '2026-03-10T10:30:00' },
        { id: 2, user_message: '工作压力好大', ai_reply: '面对压力，尝试先把让你担心的事情写下来，然后一步一步来解决。', emotion_type: 'anxious', created_at: '2026-03-10T11:00:00' },
        { id: 3, user_message: '今天和朋友吵架了', ai_reply: '愤怒时，先深呼吸冷静一下是很好的做法。', emotion_type: 'angry', created_at: '2026-03-10T14:00:00' }
    ],

    // 情绪趋势数据
    emotionTrend: {
        week: [
            { date: '03-03', overall: 80.0, anxiety: 20.0, happiness: 90.0 },
            { date: '03-04', overall: 65.0, anxiety: 45.0, happiness: 60.0 },
            { date: '03-05', overall: 55.0, anxiety: 60.0, happiness: 50.0 },
            { date: '03-06', overall: 70.0, anxiety: 35.0, happiness: 75.0 },
            { date: '03-07', overall: 75.0, anxiety: 30.0, happiness: 80.0 },
            { date: '03-08', overall: 60.0, anxiety: 50.0, happiness: 55.0 },
            { date: '03-09', overall: 72.0, anxiety: 28.0, happiness: 78.0 }
        ],
        month: [
            { date: '03-01', overall: 75.0, anxiety: 25.0, happiness: 80.0 },
            { date: '03-02', overall: 68.0, anxiety: 40.0, happiness: 65.0 },
            { date: '03-03', overall: 80.0, anxiety: 20.0, happiness: 90.0 },
            { date: '03-04', overall: 65.0, anxiety: 45.0, happiness: 60.0 },
            { date: '03-05', overall: 55.0, anxiety: 60.0, happiness: 50.0 },
            { date: '03-06', overall: 70.0, anxiety: 35.0, happiness: 75.0 },
            { date: '03-07', overall: 75.0, anxiety: 30.0, happiness: 80.0 },
            { date: '03-08', overall: 60.0, anxiety: 50.0, happiness: 55.0 },
            { date: '03-09', overall: 72.0, anxiety: 28.0, happiness: 78.0 },
            { date: '03-10', overall: 78.0, anxiety: 22.0, happiness: 85.0 }
        ],
        year: [
            { date: '1月', overall: 65.0, anxiety: 45.0, happiness: 60.0 },
            { date: '2月', overall: 70.0, anxiety: 40.0, happiness: 65.0 },
            { date: '3月', overall: 75.0, anxiety: 30.0, happiness: 78.0 }
        ]
    },

    // 疗愈方案
    healingPlan: {
        id: 1,
        tasks: [
            { id: 1, type: 'meditation', title: '晨间冥想', duration: '5分钟', completed: true },
            { id: 2, type: 'journal', title: '感恩日记', duration: '10分钟', completed: true },
            { id: 3, type: 'breathing', title: '4-7-8呼吸', duration: '5分钟', completed: false },
            { id: 4, type: 'exercise', title: '户外散步', duration: '20分钟', completed: false }
        ],
        completion_rate: 50.0,
        status: 'in_progress',
        ai_summary: '今日已完成50%的疗愈任务，继续保持！'
    },

    // 疗愈方案列表
    healingPlans: [
        { id: 1, plan_date: '2026-03-10', tasks: MockData.healingPlan.tasks, completion_rate: 50.0, status: 'in_progress', ai_summary: '今日已完成50%' },
        { id: 2, plan_date: '2026-03-09', tasks: MockData.healingPlan.tasks, completion_rate: 100.0, status: 'completed', ai_summary: '昨日任务全部完成！' },
        { id: 3, plan_date: '2026-03-08', tasks: MockData.healingPlan.tasks, completion_rate: 75.0, status: 'completed', ai_summary: '表现优秀！' }
    ],

    // 心理测评
    assessments: [
        { id: 1, assessment_type: 'PHQ-9', total_score: 5, level: 'mild', created_at: '2026-03-08T10:00:00' },
        { id: 2, assessment_type: 'GAD-7', total_score: 3, level: 'none', created_at: '2026-03-05T15:00:00' }
    ],

    // 预约列表
    appointments: [
        { id: 1, counselor_name: '张老师', appointment_time: '2026-03-15T14:00:00', consultation_type: 'video', status: 'confirmed' },
        { id: 2, counselor_name: '李老师', appointment_time: '2026-03-20T10:00:00', consultation_type: 'voice', status: 'pending' }
    ],

    // 用户统计
    userStats: {
        chat_count: 16,
        emotion_count: 30,
        assessment_count: 5,
        appointment_count: 2,
        usage_days: 7,
        emotion_distribution: {
            'happy': 8,
            'sad': 6,
            'anxious': 5,
            'angry': 3,
            'tired': 4
        }
    },

    // AI回复
    aiResponses: {
        happy: [
            "听到你今天心情不错，我也很为你高兴！有什么特别的事情想分享吗？",
            "太棒了！快乐的心情值得延续。继续保持这份好心情吧！",
            "很高兴你能感受到快乐。记得珍惜这份美好的感觉，也可以把它记录下来哦！"
        ],
        sad: [
            "我在这里陪你。难过的时候，能说出来就已经是很好的开始。",
            "感到难过是很正常的情绪，不要责怪自己。慢慢说，我在这里倾听。",
            "感谢你愿意分享你的难过。每个人都会有低潮期，你并不孤单。"
        ],
        anxious: [
            "焦虑是一种很常见的情绪。深呼吸一下，告诉我是什么让你感到焦虑呢？",
            "我能感受到你的不安。先放松一下，焦虑的时候我们更需要好好照顾自己。",
            "面对焦虑，你可以尝试先把让你担心的事情写下来，然后一步一步来解决。"
        ],
        angry: [
            "愤怒是很有力量的情绪，它可能在提醒我们某些边界被侵犯了。",
            "感受到愤怒是很正常的。给自己一点空间和时间来处理这种强烈的情绪。",
            "愤怒时，先深呼吸冷静一下是很好的做法。"
        ],
        tired: [
            "你看起来很累了。休息一下很重要，你的身心都在提醒你需要充电了。",
            "疲惫的时候，允许自己停下来很重要。你最近是不是太辛苦了呢？",
            "记得照顾好自己。如果可以的话，给自己安排一些休息时间吧。"
        ],
        default: [
            "感谢你的分享。每一种情绪都值得被看见和理解。",
            "我在这里倾听你。慢慢说，不要着急。",
            "你能愿意表达自己的情绪，这本身就是一种勇气。"
        ]
    }
};

// ==================== 工具函数 ====================
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function getRandomItem(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

// ==================== API服务类 ====================
class ApiService {
    constructor() {
        this.baseUrl = BASE_URL;
        this.useMock = USE_MOCK;
    }

    // 通用请求方法
    async request(method, path, data = null) {
        if (this.useMock) {
            // 使用Mock数据
            return this.getMockData(method, path, data);
        }

        const url = this.baseUrl + path;
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        return response.json();
    }

    // Mock数据处理
    getMockData(method, path, data) {
        return new Promise(async (resolve) => {
            await delay(300 + Math.random() * 200); // 模拟网络延迟

            // 健康检查
            if (path === '/health') {
                resolve({ status: 'ok', message: 'EmoHealer API is running (Mock)' });
                return;
            }

            // 获取用户列表
            if (method === 'GET' && path === '/users') {
                resolve({ code: 200, data: MockData.users });
                return;
            }

            // 获取用户信息
            if (method === 'GET' && path.startsWith('/user/')) {
                resolve({ code: 200, data: MockData.userInfo });
                return;
            }

            // 获取对话历史
            if (method === 'GET' && path.startsWith('/chat/history/')) {
                resolve({ code: 200, data: MockData.chatHistory });
                return;
            }

            // 发送消息
            if (method === 'POST' && path === '/chat/send') {
                const userMessage = data?.message || '';
                const emotionType = data?.emotion_type || 'default';
                
                // 简单情绪检测
                let detectedEmotion = emotionType;
                if (!detectedEmotion || emotionType === 'default') {
                    if (userMessage.includes('开心') || userMessage.includes('高兴')) detectedEmotion = 'happy';
                    else if (userMessage.includes('难过') || userMessage.includes('伤心')) detectedEmotion = 'sad';
                    else if (userMessage.includes('焦虑') || userMessage.includes('担心')) detectedEmotion = 'anxious';
                    else if (userMessage.includes('生气') || userMessage.includes('愤怒')) detectedEmotion = 'angry';
                    else if (userMessage.includes('累') || userMessage.includes('疲惫')) detectedEmotion = 'tired';
                }

                const responses = MockData.aiResponses[detectedEmotion] || MockData.aiResponses.default;
                const reply = getRandomItem(responses);

                // 危机检测
                const crisisKeywords = ['自杀', '自伤', '放弃', '不想活', '结束一切', '绝望'];
                const isCrisis = crisisKeywords.some(k => userMessage.includes(k));

                resolve({
                    reply: isCrisis ? '我感受到你正在经历非常困难的时刻。请记住，你不是一个人。建议拨打心理援助热线：400-161-9995' : reply,
                    emotion: detectedEmotion,
                    confidence: 0.85,
                    is_crisis: isCrisis,
                    timestamp: new Date().toISOString()
                });
                return;
            }

            // 情绪趋势
            if (method === 'POST' && path === '/emotion/trend') {
                const period = data?.period || 'month';
                resolve({ code: 200, data: MockData.emotionTrend[period] || MockData.emotionTrend.month });
                return;
            }

            // 疗愈方案
            if (method === 'GET' && path.startsWith('/healing-plan/')) {
                resolve({ code: 200, data: MockData.healingPlan });
                return;
            }

            // 疗愈方案列表
            if (method === 'GET' && path.startsWith('/plans/')) {
                resolve({ code: 200, data: MockData.healingPlans });
                return;
            }

            // 心理测评历史
            if (method === 'GET' && path.startsWith('/assessment/')) {
                resolve({ code: 200, data: MockData.assessments });
                return;
            }

            // 提交心理测评
            if (method === 'POST' && path === '/assessment/submit') {
                const totalScore = data?.answers?.reduce((a, b) => a + b, 0) || 0;
                resolve({ 
                    code: 200, 
                    message: '测评提交成功', 
                    data: { id: Date.now(), total_score: totalScore, level: data?.level || 'mild' } 
                });
                return;
            }

            // 预约列表
            if (method === 'GET' && path.startsWith('/appointment/')) {
                resolve({ code: 200, data: MockData.appointments });
                return;
            }

            // 提交预约
            if (method === 'POST' && path === '/appointment/submit') {
                resolve({ 
                    code: 200, 
                    message: '预约提交成功', 
                    data: { id: Date.now(), status: 'pending', appointment_time: data?.appointment_date } 
                });
                return;
            }

            // 用户统计
            if (method === 'GET' && path.startsWith('/stats/')) {
                resolve({ code: 200, data: MockData.userStats });
                return;
            }

            // 默认返回404
            resolve({ error: 'API not found', path, method });
        });
    }

    // 便捷方法
    get(path) {
        return this.request('GET', path);
    }

    post(path, data) {
        return this.request('POST', path, data);
    }

    put(path, data) {
        return this.request('PUT', path, data);
    }

    delete(path) {
        return this.request('DELETE', path);
    }
}

// ==================== 导出API实例 ====================
const API = new ApiService();

// ==================== 便捷函数 ====================
// 以下函数可直接调用，无需创建实例

async function getUserInfo(userId = 1) {
    return API.get(`/user/${userId}`);
}

async function getChatHistory(userId = 1, limit = 20) {
    return API.get(`/chat/history/${userId}?limit=${limit}`);
}

async function sendChatMessage(userId = 1, message, emotionType = null) {
    return API.post('/chat/send', { user_id: userId, message, emotion_type: emotionType });
}

async function getEmotionTrend(userId = 1, period = 'month') {
    return API.post('/emotion/trend', { user_id: userId, period });
}

async function getHealingPlan(userId = 1) {
    return API.get(`/healing-plan/${userId}`);
}

async function getHealingPlans(userId = 1) {
    return API.get(`/plans/${userId}`);
}

async function submitAssessment(userId, assessmentType, answers, level, suggestions = '') {
    return API.post('/assessment/submit', { 
        user_id: userId, 
        assessment_type: assessmentType, 
        answers, 
        level, 
        suggestions 
    });
}

async function getAssessments(userId = 1) {
    return API.get(`/assessment/${userId}`);
}

async function submitAppointment(userId, name, phone, consultationType, appointmentDate, description = '') {
    return API.post('/appointment/submit', {
        user_id: userId,
        name,
        phone,
        consultation_type: consultationType,
        appointment_date: appointmentDate,
        description
    });
}

async function getAppointments(userId = 1) {
    return API.get(`/appointment/${userId}`);
}

async function getUserStats(userId = 1) {
    return API.get(`/stats/${userId}`);
}

async function healthCheck() {
    return API.get('/health');
}

// ==================== 导出所有函数 ====================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        API,
        getUserInfo,
        getChatHistory,
        sendChatMessage,
        getEmotionTrend,
        getHealingPlan,
        getHealingPlans,
        submitAssessment,
        getAssessments,
        submitAppointment,
        getAppointments,
        getUserStats,
        healthCheck
    };
}
