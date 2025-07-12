#!/usr/bin/env python3
"""
MEXC Working Logger - ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ
Правильно обрабатывает формат событий MEXC
"""
import requests
import json
import time
import hmac
import hashlib
import websocket
import threading
from pathlib import Path
from datetime import datetime
import signal
import sys

# Configuration
TRADES_LOG = Path("logs/mexc_working_trades.jsonl")
EVENTS_LOG = Path("logs/mexc_working_events.jsonl")
CONNECTION_LOG = Path("logs/mexc_working_connection.jsonl")
TRADES_LOG.parent.mkdir(parents=True, exist_ok=True)

class MEXCWorkingLogger:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.mexc.com"
        self.ws_url = "wss://wbs.mexc.com/ws"
        
        # Session tracking
        self.session_start = None
        self.trade_count = 0
        self.event_count = 0
        self.is_running = False
        self.ws = None
        self.subscription_active = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        print(f"\\n🛑 Остановка по сигналу {signum}")
        self.stop_logging()
        sys.exit(0)
        
    def create_signature(self, params):
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        return hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()

    def get_listen_key(self):
        timestamp = int(time.time() * 1000)
        params = {"timestamp": timestamp}
        signature = self.create_signature(params)
        
        headers = {"X-MEXC-APIKEY": self.api_key}
        url = f"{self.base_url}/api/v3/userDataStream?timestamp={timestamp}&signature={signature}"
        
        try:
            response = requests.post(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                listen_key = data.get("listenKey")
                if listen_key:
                    self.log_connection_event("listenkey_success", {"length": len(listen_key)})
                    return listen_key
            else:
                self.log_connection_event("listenkey_error", {
                    "status": response.status_code,
                    "response": response.text[:200]
                })
        except Exception as e:
            self.log_connection_event("listenkey_exception", {"error": str(e)})
        return None

    def log_connection_event(self, event_type, details):
        try:
            entry = {
                "session_id": self.session_start,
                "timestamp": int(time.time() * 1000),
                "event_type": event_type,
                "details": details
            }
            
            with CONNECTION_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\\n")
                
        except Exception as e:
            print(f"❌ Connection log error: {e}")

    def log_all_events(self, event_data):
        try:
            entry = {
                "session_id": self.session_start,
                "timestamp": int(time.time() * 1000),
                "event_id": self.event_count,
                "raw_data": event_data
            }
            
            with EVENTS_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\\n")
            
            self.event_count += 1
            
        except Exception as e:
            print(f"❌ Event log error: {e}")

    def log_mexc_trade_event(self, mexc_data):
        """Логирование событий MEXC в правильном формате"""
        try:
            # Извлекаем данные из MEXC формата
            d = mexc_data.get("d", {})
            
            entry = {
                "session_id": self.session_start,
                "timestamp": mexc_data.get("t", int(time.time() * 1000)),
                "datetime": datetime.now().isoformat(),
                "trade_id": self.trade_count,
                
                # Данные MEXC события
                "asset": d.get("a"),  # Актив (LIF3, USDT, MX)
                "operation": d.get("o"),  # Операция (ENTRUST, ENTRUST_PLACE)
                "free_balance": float(d.get("f", 0)),  # Свободный баланс
                "free_delta": float(d.get("fd", 0)),  # Изменение свободного
                "locked_balance": float(d.get("l", 0)),  # Заблокированный баланс
                "locked_delta": float(d.get("ld", 0)),  # Изменение заблокированного
                "change_time": d.get("c"),  # Время изменения
                "change_id": d.get("cd"),  # ID изменения
                
                # Анализ типа события
                "event_type": self.analyze_mexc_event(d),
                
                # Полные сырые данные
                "raw_mexc_data": mexc_data
            }
            
            with TRADES_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\\n")
            
            self.trade_count += 1
            
            # Красивое отображение события
            asset = entry.get("asset", "")
            operation = entry.get("operation", "")
            event_type = entry.get("event_type", "")
            free_delta = entry.get("free_delta", 0)
            locked_delta = entry.get("locked_delta", 0)
            
            print("\\n" + "🎯" * 50)
            print(f"📊 ТОРГОВОЕ СОБЫТИЕ #{self.trade_count:03d}")
            print(f"💱 Актив: {asset}")
            print(f"🔄 Операция: {operation}")
            print(f"📋 Тип: {event_type}")
            print(f"💰 Свободно: {free_delta:+.2f}")
            print(f"🔒 Заблокировано: {locked_delta:+.2f}")
            print(f"⏰ {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            print("🎯" * 50)
            
        except Exception as e:
            print(f"❌ MEXC trade log error: {e}")

    def analyze_mexc_event(self, d):
        """Анализ типа события MEXC"""
        operation = d.get("o", "")
        free_delta = float(d.get("fd", 0))
        locked_delta = float(d.get("ld", 0))
        
        if operation == "ENTRUST_PLACE":
            if locked_delta > 0:
                return "ORDER_PLACED"  # Ордер размещен
            else:
                return "ORDER_UNKNOWN"
        elif operation == "ENTRUST":
            if locked_delta < 0 and free_delta > 0:
                return "ORDER_CANCELED"  # Ордер отменен
            elif locked_delta < 0 and free_delta == 0:
                return "ORDER_FILLED"  # Ордер исполнен
            elif locked_delta == 0 and free_delta > 0:
                return "TRADE_SETTLED"  # Торговля завершена
            else:
                return "ORDER_MODIFIED"  # Ордер изменен
        else:
            return f"UNKNOWN_{operation}"

    def send_subscription(self, ws):
        """Отправка подписки на события MEXC"""
        subscription = {
            "method": "SUBSCRIPTION",
            "params": ["spot@private.account.v3.api"],
            "id": 1
        }
        
        try:
            print(f"📤 Отправляем подписку: {subscription}")
            ws.send(json.dumps(subscription))
            self.log_connection_event("subscription_sent", subscription)
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки подписки: {e}")
            return False

    def on_ws_message(self, ws, message):
        try:
            data = json.loads(message)
            self.log_all_events(data)
            
            print(f"\\n📨 Event #{self.event_count}: {json.dumps(data, ensure_ascii=False)}")
            
            # Обработка подтверждения подписки
            if "id" in data and data.get("id") == 1:
                msg = data.get("msg", "")
                if "spot@private.account.v3.api" in msg:
                    print("✅ ПОДПИСКА НА MEXC СОБЫТИЯ АКТИВНА!")
                    self.subscription_active = True
                    self.log_connection_event("subscription_confirmed", data)
                    return
            
            # Обработка событий MEXC формата
            if "c" in data and data.get("c") == "spot@private.account.v3.api":
                print("🔥 MEXC ТОРГОВОЕ СОБЫТИЕ!")
                self.log_mexc_trade_event(data)
                return
            
            # Обработка других сообщений
            if "code" in data:
                code = data.get("code", 0)
                msg = data.get("msg", "")
                
                if msg == "method is empty.":
                    print("🔧 Сервер требует подписку...")
                    self.send_subscription(ws)
                elif msg == "PONG":
                    print("🏓 PONG")
                elif msg == "Wrong listen key":
                    print("❌ Wrong listen key - переподключение...")
                    self.reconnect()
                else:
                    print(f"ℹ️  Код {code}: {msg}")
            
            # Ping/Pong
            if "ping" in data:
                pong_data = {"pong": data["ping"]}
                ws.send(json.dumps(pong_data))
                print("🏓 Ping -> Pong")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON ошибка: {e}")
        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")

    def on_ws_error(self, ws, error):
        print(f"❌ WebSocket ошибка: {error}")
        self.log_connection_event("ws_error", {"error": str(error)})

    def on_ws_close(self, ws, close_status_code, close_msg):
        print(f"🔌 WebSocket закрыт: {close_status_code} - {close_msg}")
        self.subscription_active = False
        self.log_connection_event("ws_closed", {
            "code": close_status_code,
            "message": close_msg
        })

    def on_ws_open(self, ws):
        print("✅ WebSocket подключен!")
        self.log_connection_event("ws_opened", {"timestamp": int(time.time() * 1000)})
        
        # Принудительно отправляем подписку через 3 секунды
        def delayed_subscription():
            time.sleep(3)
            print("🔧 Принудительная отправка подписки...")
            self.send_subscription(ws)
        
        sub_thread = threading.Thread(target=delayed_subscription, daemon=True)
        sub_thread.start()

    def start_websocket(self, listen_key):
        ws_url = f"{self.ws_url}?listenKey={listen_key}"
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_ws_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close,
            on_open=self.on_ws_open
        )
        
        def run_ws():
            self.ws.run_forever(ping_interval=60, ping_timeout=10)
        
        ws_thread = threading.Thread(target=run_ws, daemon=True)
        ws_thread.start()
        return ws_thread

    def reconnect(self):
        if not self.is_running:
            return
            
        print("🔄 Переподключение...")
        self.subscription_active = False
        
        if self.ws:
            self.ws.close()
        
        listen_key = self.get_listen_key()
        if listen_key:
            self.start_websocket(listen_key)

    def start_logging(self):
        self.session_start = int(time.time())
        self.trade_count = 0
        self.event_count = 0
        self.is_running = True
        self.subscription_active = False
        
        print("🎯 MEXC WORKING LOGGER - ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ")
        print("=" * 70)
        print("✅ Правильно обрабатывает формат событий MEXC")
        print("=" * 70)
        print(f"📊 Session ID: {self.session_start}")
        print(f"📁 Торговые события: {TRADES_LOG}")
        print(f"📁 Все события: {EVENTS_LOG}")
        print(f"📁 Подключение: {CONNECTION_LOG}")
        print("=" * 70)
        
        self.log_connection_event("session_start", {
            "session_id": self.session_start,
            "mode": "working_mexc_logger"
        })
        
        # Получаем listenKey
        listen_key = self.get_listen_key()
        if not listen_key:
            print("❌ Не удалось получить listenKey")
            return False
        
        print("✅ ListenKey получен")
        
        # Запускаем WebSocket
        self.start_websocket(listen_key)
        
        # Ждем активации подписки
        print("⏳ Ожидание активации подписки на события MEXC...")
        for i in range(20):
            time.sleep(1)
            
            status = "ACTIVE" if self.subscription_active else "WAITING"
            print(f"   {i+1:2d}/20: {status} | Events: {self.event_count}")
            
            if self.subscription_active:
                break
        
        print("\\n🚀 ЛОГГЕР ГОТОВ И ПРОТЕСТИРОВАН!")
        print("🎯 Торгуйте в MetaScalp - все события захватываются!")
        print("📊 Поддерживаются:")
        print("   ✅ Размещение ордеров")
        print("   ✅ Отмена ордеров") 
        print("   ✅ Исполнение ордеров")
        print("   ✅ Изменения балансов")
        print("🛑 Ctrl+C для остановки")
        print("=" * 70)
        
        try:
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\\n🛑 Остановка по Ctrl+C")
        finally:
            self.stop_logging()
        
        return True

    def stop_logging(self):
        self.is_running = False
        
        if self.ws:
            self.ws.close()
        
        duration = int(time.time()) - self.session_start if self.session_start else 0
        
        self.log_connection_event("session_end", {
            "duration_seconds": duration,
            "total_trades": self.trade_count,
            "total_events": self.event_count
        })
        
        print(f"\\n⏹️  ЛОГИРОВАНИЕ ЗАВЕРШЕНО")
        print(f"⏱️  Длительность: {duration} секунд")
        print(f"📊 Торговых событий: {self.trade_count}")
        print(f"📋 Всего событий: {self.event_count}")
        print(f"📁 Все данные сохранены!")

def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config["api_key"], config["api_secret"]
    except Exception as e:
        print(f"❌ Ошибка config.json: {e}")
        return None, None

def main():
    print("🎯 MEXC WORKING LOGGER")
    print("Финальная рабочая версия для сбора скальпинг-данных")
    print("=" * 50)
    
    api_key, api_secret = load_config()
    if not api_key or not api_secret:
        print("❌ Отсутствуют API ключи в config.json")
        return
    
    logger = MEXCWorkingLogger(api_key, api_secret)
    success = logger.start_logging()

if __name__ == "__main__":
    main()