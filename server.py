#!/usr/bin/env python3
"""北京之行问卷服务器 — 提供问卷页面 + 收集提交 + 查看结果"""
import json
import os
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "responses.json")
RESULTS_PASSWORD = "beijing2025"

HTML_TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh; padding: 20px;
  }}
  .container {{ max-width: 720px; margin: 0 auto; }}
  .header {{ text-align: center; color: white; padding: 30px 20px 20px; }}
  .header h1 {{ font-size: 1.8em; margin-bottom: 6px; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
  .header p {{ opacity: 0.9; font-size: 0.95em; }}
  .card {{
    background: white; border-radius: 16px; padding: 28px 24px; margin-bottom: 18px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.12);
  }}
  .card h2 {{ font-size: 1.2em; color: #333; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }}
  .form-group {{ margin-bottom: 20px; }}
  .form-group:last-child {{ margin-bottom: 0; }}
  label.block {{ display: block; font-weight: 600; color: #444; margin-bottom: 8px; }}
  .options {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .option-btn {{ flex: 1; min-width: 70px; }}
  .option-btn input {{ display: none; }}
  .option-btn label {{
    display: block; text-align: center; padding: 10px 6px; border: 2px solid #e0e0e0;
    border-radius: 10px; cursor: pointer; font-weight: 500; color: #555;
    transition: all 0.2s; font-size: 0.9em;
  }}
  .option-btn input:checked + label {{ border-color: #667eea; background: #667eea; color: white; box-shadow: 0 3px 10px rgba(102,126,234,0.3); }}
  .option-btn label:hover {{ border-color: #667eea; background: #f0f0ff; }}
  .option-btn input:checked + label:hover {{ background: #667eea; }}
  textarea {{
    width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 10px;
    font-size: 0.95em; font-family: inherit; resize: vertical; min-height: 90px;
    transition: border-color 0.2s;
  }}
  textarea:focus, input[type="text"]:focus, input[type="tel"]:focus {{ outline: none; border-color: #667eea; }}
  input[type="text"], input[type="tel"] {{
    width: 100%; padding: 11px 14px; border: 2px solid #e0e0e0; border-radius: 10px;
    font-size: 0.95em; font-family: inherit; box-sizing: border-box; transition: border-color 0.2s;
  }}
  .reference-box {{ background: #f8f9ff; border: 1px solid #e0e3ff; border-radius: 12px; padding: 18px; margin-bottom: 18px; }}
  .reference-box h3 {{ color: #667eea; margin-bottom: 12px; font-size: 0.95em; }}
  .ref-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
  @media (max-width: 500px) {{ .ref-grid {{ grid-template-columns: 1fr; }} }}
  .ref-col h4 {{ font-size: 0.9em; color: #555; margin-bottom: 8px; padding-bottom: 5px; border-bottom: 1px dashed #d0d0ff; }}
  .ref-list {{ list-style: none; font-size: 0.85em; color: #666; line-height: 1.85; }}
  .ref-list li::before {{ content: "▸ "; color: #667eea; font-size: 0.8em; }}
  .ref-list li span {{ color: #999; font-size: 0.85em; }}
  .submit-btn {{
    display: block; width: 100%; padding: 14px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white; border: none; border-radius: 12px; font-size: 1.1em; font-weight: 600;
    cursor: pointer; transition: transform 0.1s, box-shadow 0.2s;
    box-shadow: 0 5px 18px rgba(102,126,234,0.35);
  }}
  .submit-btn:hover {{ transform: translateY(-1px); box-shadow: 0 7px 22px rgba(102,126,234,0.45); }}
  .submit-btn:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
  .success-msg {{ display: none; text-align: center; padding: 30px 20px; }}
  .success-msg .icon {{ font-size: 2.5em; margin-bottom: 12px; }}
  .success-msg h2 {{ color: #333; margin-bottom: 8px; border: none; }}
  .footer {{ text-align: center; color: rgba(255,255,255,0.7); font-size: 0.8em; padding: 10px 0 25px; }}

  /* results page */
  .resp-card {{
    background: white; border-radius: 12px; padding: 18px 20px; margin-bottom: 14px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08); border-left: 4px solid #667eea;
  }}
  .resp-card .r-time {{ color: #999; font-size: 0.82em; margin-bottom: 8px; }}
  .resp-card .r-item {{ margin-bottom: 5px; font-size: 0.92em; }}
  .resp-card .r-item strong {{ color: #555; }}
  .resp-card .r-dream {{ margin-top: 8px; padding: 10px 12px; background: #f8f9ff; border-radius: 8px; font-size: 0.9em; color: #555; white-space: pre-wrap; }}
  .stats-box {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }}
  .stat-item {{
    background: white; border-radius: 10px; padding: 12px 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); font-size: 0.9em;
  }}
  .stat-item strong {{ color: #667eea; }}
  .password-form {{ text-align: center; padding: 40px; }}
  .password-form input {{
    padding: 10px 16px; border: 2px solid #e0e0e0; border-radius: 8px;
    font-size: 1em; width: 200px; text-align: center;
  }}
  .password-form button {{
    padding: 10px 24px; background: #667eea; color: white; border: none;
    border-radius: 8px; font-size: 1em; cursor: pointer; margin-left: 8px;
  }}
  .error {{ color: #e74c3c; font-size: 0.9em; margin-top: 8px; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


class SurveyHandler(SimpleHTTPRequestHandler):
    """处理问卷请求的自定义 handler"""

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/" or path == "/index.html":
            self.serve_survey()
        elif path == "/results":
            self.serve_results()
        elif path == "/responses.json":
            self.serve_json()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/submit":
            self.handle_submit()
        else:
            self.send_error(404)

    def serve_survey(self):
        body = """<div class="container">
  <div class="header">
    <h1>🏯 北京之行 · 出行意向问卷</h1>
    <p>请各位家人填写，方便我们统一安排行程 ~</p>
  </div>

  <form id="sf" action="/submit" method="POST" onsubmit="return handleSubmit()">
    <div class="card">
      <h2>👤 1. 基本信息</h2>
      <div class="form-group">
        <label class="block">姓名：</label>
        <input type="text" name="realname" required placeholder="请输入姓名">
      </div>
      <div class="form-group">
        <label class="block">身份证号码：</label>
        <input type="text" name="idcard" required placeholder="请输入身份证号码">
      </div>
      <div class="form-group">
        <label class="block">手机号码：</label>
        <input type="tel" name="phone" required placeholder="请输入手机号码">
      </div>
      <div style="margin-top:8px;padding:8px 12px;background:#f0f4ff;border-radius:8px;font-size:0.8em;color:#667eea;">
        🔒 以上信息仅用于订票和旅行安排，数据仅保存在发起人本地电脑，不会上传到任何第三方平台。
      </div>
    </div>

    <div class="card">
      <h2>📅 2. 选择出发日期</h2>
      <div class="form-group">
        <label class="block">请选择您希望出发的日期（单选）：</label>
        <div class="options">
          <div class="option-btn"><input type="radio" name="date" value="6月1日(周日)" id="d1" required><label for="d1">6月1日<br>周日</label></div>
          <div class="option-btn"><input type="radio" name="date" value="6月2日(周一)" id="d2"><label for="d2">6月2日<br>周一</label></div>
          <div class="option-btn"><input type="radio" name="date" value="6月3日(周二)" id="d3"><label for="d3">6月3日<br>周二</label></div>
          <div class="option-btn"><input type="radio" name="date" value="6月4日(周三)" id="d4"><label for="d4">6月4日<br>周三</label></div>
          <div class="option-btn"><input type="radio" name="date" value="6月5日(周四)" id="d5"><label for="d5">6月5日<br>周四</label></div>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>⏰ 3. 出发时段偏好</h2>
      <div class="form-group">
        <label class="block">您想在哪段时间出发？（单选）：</label>
        <div class="options">
          <div class="option-btn"><input type="radio" name="time" value="上午 6:00-12:00" id="t1" required><label for="t1">🌅 上午<br>6:00-12:00</label></div>
          <div class="option-btn"><input type="radio" name="time" value="中午 12:00-14:00" id="t2"><label for="t2">☀️ 中午<br>12:00-14:00</label></div>
          <div class="option-btn"><input type="radio" name="time" value="下午 14:00-18:00" id="t3"><label for="t3">🌤 下午<br>14:00-18:00</label></div>
          <div class="option-btn"><input type="radio" name="time" value="晚上 18:00-24:00" id="t4"><label for="t4">🌙 晚上<br>18:00以后</label></div>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>🚄 4. 出行方式</h2>
      <div class="form-group">
        <label class="block">您倾向哪种交通方式？（单选）：</label>
        <div class="options">
          <div class="option-btn"><input type="radio" name="transport" value="高铁/动车" id="m1" required><label for="m1">🚄 高铁/动车</label></div>
          <div class="option-btn"><input type="radio" name="transport" value="飞机" id="m2"><label for="m2">✈️ 飞机</label></div>
        </div>
      </div>
      <div style="margin-top:10px; padding:10px 14px; background:#fffbe6; border-radius:8px; font-size:0.85em; color:#8a6d14;">
        💡 <strong>参考：</strong>广元/成都出发动车约7-10h，飞机约2.5h；深圳/广州/珠海出发动车约8-11h，飞机约3h。
      </div>
    </div>

    <div class="card">
      <h2>📍 5. 出发城市</h2>
      <div class="form-group">
        <label class="block">您从哪个城市出发？（单选）：</label>
        <div class="options">
          <div class="option-btn"><input type="radio" name="city" value="广元" id="c1" required><label for="c1">🏔 广元</label></div>
          <div class="option-btn"><input type="radio" name="city" value="成都" id="c2"><label for="c2">🐼 成都</label></div>
          <div class="option-btn"><input type="radio" name="city" value="深圳" id="c3"><label for="c3">🏙 深圳</label></div>
          <div class="option-btn"><input type="radio" name="city" value="珠海" id="c4"><label for="c4">🌊 珠海</label></div>
          <div class="option-btn"><input type="radio" name="city" value="广州" id="c5"><label for="c5">🌆 广州</label></div>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>🎯 6. 在北京想去的地方 & 想吃的美食</h2>

      <div class="reference-box">
        <h3>📖 北京热门参考（供选择时参考~）</h3>
        <div class="ref-grid">
          <div class="ref-col">
            <h4>🏛 经典必去景点</h4>
            <ul class="ref-list">
              <li>故宫 <span>— 明清皇宫，建议提前7天预约</span></li>
              <li>天安门广场 <span>— 看升旗仪式（需早起）</span></li>
              <li>八达岭长城 <span>— "不到长城非好汉"</span></li>
              <li>慕田峪长城 <span>— 人少景美，有滑道下山</span></li>
              <li>颐和园 <span>— 皇家园林，昆明湖划船</span></li>
              <li>天坛 <span>— 祈年殿标志性建筑</span></li>
              <li>恭王府 <span>— 和珅旧宅，摸福字碑</span></li>
              <li>雍和宫 <span>— 北京最大藏传佛教寺院</span></li>
            </ul>
          </div>
          <div class="ref-col">
            <h4>🎨 文艺 & 潮流地标</h4>
            <ul class="ref-list">
              <li>南锣鼓巷 <span>— 老胡同+文创小店</span></li>
              <li>798艺术区 <span>— 当代艺术画廊展览</span></li>
              <li>后海 / 什刹海 <span>— 酒吧街+夜景散步</span></li>
              <li>五道营胡同 <span>— 小众咖啡馆聚集地</span></li>
              <li>国家博物馆 <span>— 镇馆之宝无数，需预约</span></li>
              <li>环球影城 <span>— 哈利波特、变形金刚主题</span></li>
              <li>鸟巢 / 水立方 <span>— 奥运地标，夜景很美</span></li>
              <li>三里屯 <span>— 潮流购物+餐厅酒吧</span></li>
            </ul>
          </div>
          <div class="ref-col">
            <h4>🍗 必吃美食 · 正餐</h4>
            <ul class="ref-list">
              <li>北京烤鸭 <span>— 全聚德/便宜坊/大董/四季民福</span></li>
              <li>涮羊肉 <span>— 东来顺/聚宝源，铜锅炭火</span></li>
              <li>炸酱面 <span>— 海碗居/老北京炸酱面馆</span></li>
              <li>炒肝+包子 <span>— 姚记炒肝（鼓楼旁边）</span></li>
              <li>卤煮火烧 <span>— 小肠陈/门框胡同</span></li>
              <li>爆肚 <span>— 爆肚冯/金生隆</span></li>
              <li>京酱肉丝 <span>— 甜面酱炒肉丝配豆腐皮</span></li>
              <li>乾隆白菜 <span>— 芝麻酱拌白菜，爽口</span></li>
            </ul>
          </div>
          <div class="ref-col">
            <h4>🍡 小吃 & 甜品</h4>
            <ul class="ref-list">
              <li>糖葫芦 <span>— 经典街头小吃</span></li>
              <li>驴打滚 <span>— 糯米豆沙，软糯香甜</span></li>
              <li>艾窝窝 <span>— 糯米包芝麻糖馅</span></li>
              <li>门钉肉饼 <span>— 皮薄肉厚，汁多味美</span></li>
              <li>老北京酸奶 <span>— 瓷罐装，街头小卖部有售</span></li>
              <li>豌豆黄 <span>— 清凉细腻的豌豆糕</span></li>
              <li>炸灌肠 <span>— 蘸蒜汁吃，外焦里嫩</span></li>
              <li>豆汁儿+焦圈 <span>— 老磁器口豆汁店（慎入！）</span></li>
            </ul>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label class="block">请填写您特别想去的地方 & 特别想吃的美食（也可以写上面没有提到的）：</label>
        <textarea name="dream" placeholder="例如：&#10;想去：故宫、长城、798艺术区&#10;想吃：北京烤鸭（全聚德）、涮羊肉（东来顺）、炸酱面&#10;其他想法：想体验一下胡同文化，坐黄包车逛后海..."></textarea>
      </div>
    </div>

    <div class="card">
      <h2>💬 7. 你想对这次旅行说的一句话</h2>
      <div class="form-group">
        <label class="block">用一句话或一个词表达你对这次北京之行的期待、心情或想法：</label>
        <input type="text" name="oneword" placeholder="例如：期待已久！ / 一家人整整齐齐 / 开心 / 想去长城当一次好汉...">
      </div>
    </div>

    <button type="submit" class="submit-btn" id="sb">✅ 提交问卷</button>
  </form>

  <div class="card" id="sm" style="display:none;">
    <div style="text-align:center;padding:20px 0;">
      <div style="font-size:3em;margin-bottom:12px;">🎉</div>
      <h2 style="color:#333;margin-bottom:6px;border:none;">提交成功！</h2>
      <p style="color:#666;margin-bottom:20px;">感谢填写，已收到您的出行偏好~</p>
      <div style="background:#f8f9ff;border-radius:12px;padding:20px;text-align:left;max-width:400px;margin:0 auto;">
        <div style="font-size:0.9em;color:#555;line-height:2.2;" id="smSummary"></div>
      </div>
    </div>
  </div>

  <div class="footer">问卷数据仅供家人出行安排使用 · v2.3 · 提交后可联系发起人修改</div>
</div>

<script>
function handleSubmit() {
  var fd = new FormData(document.getElementById('sf'));
  var required = ['realname', 'idcard', 'phone', 'date', 'time', 'transport', 'city'];
  var labels = {
    realname: '姓名', idcard: '身份证号码', phone: '手机号码',
    date: '出发日期', time: '出发时段', transport: '出行方式', city: '出发城市'
  };
  var missing = [];
  for (var i = 0; i < required.length; i++) {
    var v = fd.get(required[i]);
    if (!v || (typeof v === 'string' && v.trim() === '')) {
      missing.push('【' + labels[required[i]] + '】');
    }
  }
  if (missing.length > 0) {
    alert('以下必填项还未填写或选择，请检查：\n\n' + missing.join('\n'));
    return false;
  }

  var b = document.getElementById('sb');
  b.disabled = true;
  b.textContent = '提交中...';

  if (typeof fetch === 'undefined') {
    // 老浏览器不支持 fetch，走原生提交（会有 JSON 返回，但数据能送达）
    return true;
  }

  fetch('/submit', { method: 'POST', body: fd })
    .then(function(r) {
      if (r.ok) {
        return r.json().then(function() {
          var cards = document.querySelectorAll('.card');
          for (var j = 0; j < cards.length; j++) {
            if (cards[j].id !== 'sm') { cards[j].style.display = 'none'; }
          }
          b.style.display = 'none';
          document.getElementById('sm').style.display = 'block';
          document.getElementById('smSummary').innerHTML =
            '<strong>姓名：</strong>' + (fd.get('realname') || '') + '<br>' +
            '<strong>出发日期：</strong>' + (fd.get('date') || '') + '<br>' +
            '<strong>出发时段：</strong>' + (fd.get('time') || '') + '<br>' +
            '<strong>出行方式：</strong>' + (fd.get('transport') || '') + '<br>' +
            '<strong>出发城市：</strong>' + (fd.get('city') || '') + '<br>' +
            '<strong>一句话：</strong>' + (fd.get('oneword') || '（未填）');
        });
      } else {
        return r.json().then(function(data) {
          alert(data.error || '提交失败，请重试');
        });
      }
    })
    .catch(function(err) {
      alert('提交失败，请检查网络后重试，或直接联系发起人。');
    })
    .then(function() {
      b.disabled = false;
      b.textContent = '✅ 提交问卷';
    });

  return false;
}
</script>"""
        html = HTML_TPL.format(title="北京之行 · 出行意向问卷", body=body)
        self._send_html(html)

    def handle_submit(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(body)

        record = {
            "id": int(time.time() * 1000),
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "name": params.get("realname", [""])[0].strip(),
            "idcard": params.get("idcard", [""])[0].strip(),
            "phone": params.get("phone", [""])[0].strip(),
            "date": params.get("date", [""])[0],
            "time_pref": params.get("time", [""])[0],
            "transport": params.get("transport", [""])[0],
            "city": params.get("city", [""])[0],
            "dream": params.get("dream", [""])[0],
            "oneword": params.get("oneword", [""])[0],
        }

        # 服务端校验：拒绝空必填项
        required = {
            "name": "姓名", "idcard": "身份证号码", "phone": "手机号码",
            "date": "出发日期", "time_pref": "出发时段",
            "transport": "出行方式", "city": "出发城市"
        }
        for field, label in required.items():
            if not record[field]:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(
                    {"ok": False, "error": f"请填写：{label}"},
                    ensure_ascii=False
                ).encode())
                return

        # 保存
        records = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except (json.JSONDecodeError, IOError):
                records = []
        records.append(record)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}, ensure_ascii=False).encode())

    def serve_results(self):
        # 简易密码验证
        query = self.path.split("?", 1)[1] if "?" in self.path else ""
        params = parse_qs(query)
        pw = params.get("pw", [""])[0]

        if pw != RESULTS_PASSWORD:
            body = """<div class="container">
  <div class="header"><h1>🔒 查看问卷结果</h1><p>请输入密码</p></div>
  <div class="card password-form">
    <form method="GET" action="/results">
      <input type="password" name="pw" placeholder="请输入查看密码" required autofocus>
      <button type="submit">确认</button>
      <div class="error">{error}</div>
    </form>
  </div>
</div>""".format(error="密码错误，请重试" if pw else "")
            html = HTML_TPL.format(title="查看结果", body=body)
            self._send_html(html)
            return

        # 读取数据
        records = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except (json.JSONDecodeError, IOError):
                records = []

        # 统计
        date_counts = {}
        city_counts = {}
        transport_counts = {}
        time_counts = {}
        for r in records:
            date_counts[r["date"]] = date_counts.get(r["date"], 0) + 1
            city_counts[r["city"]] = city_counts.get(r["city"], 0) + 1
            transport_counts[r["transport"]] = transport_counts.get(r["transport"], 0) + 1
            time_counts[r["time_pref"]] = time_counts.get(r["time_pref"], 0) + 1

        def fmt_counts(d):
            return " | ".join(f"{k}: {v}票" for k, v in sorted(d.items())) if d else "暂无数据"

        body_parts = ['<div class="container"><div class="header"><h1>📊 问卷结果汇总</h1><p>共 <strong>{}</strong> 人已填写 &nbsp;|&nbsp; <a href="/results?pw={}" style="color:#fff;">刷新</a></p></div>'.format(len(records), RESULTS_PASSWORD)]

        # 统计卡片
        body_parts.append('<div class="card"><h2>📈 快速统计</h2><div class="stats-box">')
        body_parts.append('<div class="stat-item">📅 <strong>日期分布：</strong><br>{}</div>'.format(fmt_counts(date_counts)))
        body_parts.append('<div class="stat-item">⏰ <strong>时段分布：</strong><br>{}</div>'.format(fmt_counts(time_counts)))
        body_parts.append('<div class="stat-item">🚄 <strong>出行方式：</strong><br>{}</div>'.format(fmt_counts(transport_counts)))
        body_parts.append('<div class="stat-item">📍 <strong>出发城市：</strong><br>{}</div>'.format(fmt_counts(city_counts)))
        body_parts.append('</div></div>')

        # 个人详情
        body_parts.append('<div class="card"><h2>📋 个人详情（{}条）</h2>'.format(len(records)))
        if not records:
            body_parts.append('<p style="color:#999;text-align:center;padding:20px;">还没有人提交，分享链接给家人吧~</p>')
        for r in reversed(records):
            body_parts.append("""<div class="resp-card">
  <div class="r-time">{time} · 第{idx}份</div>
  <div class="r-item"><strong>姓名：</strong>{name} &nbsp;|&nbsp; <strong>电话：</strong>{phone}</div>
  <div class="r-item"><strong>身份证：</strong>{idcard}</div>
  <div class="r-item"><strong>出发日期：</strong>{date} &nbsp;|&nbsp; <strong>时段：</strong>{tp}</div>
  <div class="r-item"><strong>出行方式：</strong>{tr} &nbsp;|&nbsp; <strong>出发城市：</strong>{city}</div>
  <div class="r-dream"><strong>想去的地方 & 想吃的美食：</strong><br>{dream}</div>
  <div class="r-dream" style="background:#fffbe6;"><strong>💬 最想说的一句话：</strong>{oneword}</div>
</div>""".format(
                time=r["time"], idx=r.get("id", ""),
                name=r.get("name", ""), phone=r.get("phone", ""), idcard=r.get("idcard", ""),
                date=r["date"], tp=r["time_pref"], tr=r["transport"],
                city=r["city"], dream=r["dream"] or "（未填写）",
                oneword=r.get("oneword", "") or "（未填写）"
            ))
        body_parts.append('</div>')

        body_parts.append("""<div class="card" style="text-align:center;font-size:0.85em;color:#999;">
  💡 提示：将此页面链接中的 <code>pw={}</code> 去掉后分享，他人需输入密码才能看到结果。
</div>""".format(RESULTS_PASSWORD))

        body_parts.append("""<div class="footer" style="color:#666;">北京之行 · 问卷结果</div></div>""")

        html = HTML_TPL.format(title="问卷结果", body="\n".join(body_parts))
        self._send_html(html)

    def serve_json(self):
        """返回原始 JSON 数据"""
        if not os.path.exists(DATA_FILE):
            self.send_error(404)
            return
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(data.encode())

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = 8899
    server = HTTPServer(("0.0.0.0", port), SurveyHandler)
    print(f"✅ 问卷服务器已启动: http://localhost:{port}")
    print(f"📊 查看结果: http://localhost:{port}/results?pw={RESULTS_PASSWORD}")
    print(f"🔑 结果页密码: {RESULTS_PASSWORD}")
    print(f"📁 数据文件: {DATA_FILE}")
    print(f"💡 用 localtunnel 或 ngrok 暴露到公网即可分享给家人")
    print(f"  例: npx localtunnel --port {port}")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务器已关闭")
        server.server_close()


if __name__ == "__main__":
    main()
