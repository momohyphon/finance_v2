import subprocess
import time
import os
import sys

# 설정
scripts = ["finance.py", "news_kr.py", "news_us.py", "rs_kr.py", "rs_us.py"]
RESTART_INTERVAL = 600  # 10분 (600초) 대기 후 재실행

def run_invest_cycle():
    print(f"\n✨ [{time.strftime('%H:%M:%S')}] 새로운 데이터 수집 사이클을 시작합니다.")
    processes = []

    # 1. 모든 일꾼 투입
    for script in scripts:
        if os.path.exists(script):
            try:
                # 넉넉한 처리를 위해 프로세스 실행
                p = subprocess.Popen([sys.executable, script])
                processes.append((script, p))
                print(f"✅ {script} 가동 시작")
                time.sleep(5)  # 서버 부하 방지를 위해 실행 간격을 5초로 늘림
            except Exception as e:
                print(f"❌ {script} 실행 에러: {e}")
        else:
            print(f"⚠️ 파일 없음: {script}")

    # 2. 모든 일꾼이 일을 끝낼 때까지 대기 (동기화)
    print("⏳ 모든 작업이 완료될 때까지 기다리는 중...")
    for name, p in processes:
        try:
            p.wait(timeout=300) # 각 스크립트당 최대 5분 대기
            print(f"🏁 {name} 작업 완료")
        except subprocess.TimeoutExpired:
            print(f"🚨 {name} 응답 시간 초과! 강제 종료합니다.")
            p.kill()

    print(f"😴 사이클 종료. {RESTART_INTERVAL // 60}분간 휴식 후 다시 시작합니다.")
    time.sleep(RESTART_INTERVAL)

# 무한 루프 감시
if __name__ == "__main__":
    print("🚀 [투자 터미널 시스템] 엔진이 영구 가동 모드로 진입합니다.")
    try:
        while True:
            run_invest_cycle()
    except KeyboardInterrupt:
        print("\n🛑 사용자가 시스템을 수동으로 종료했습니다.")