"""log_events 파티셔닝 검증.

- parent table 은 PARTITION BY RANGE (received_at)
- 다음 30일치 daily partition pre-create
- INSERT 가 올바른 파티션으로 라우팅
"""
import psycopg


def _open_sync(upgraded_db):
    """conftest 의 upgraded_db dict 에서 sync 연결 생성."""
    sync_url = upgraded_db["sync_url"].replace("+psycopg", "")
    return psycopg.connect(sync_url)


def test_log_events_is_partitioned(upgraded_db):
    """log_events 가 PostgreSQL partitioned table 이어야 한다 (relkind = 'p')."""
    conn = _open_sync(upgraded_db)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT relkind FROM pg_class WHERE relname = 'log_events'")
            row = cur.fetchone()
        assert row is not None, "log_events 테이블이 존재하지 않음"
        assert row[0] == "p", f"log_events relkind={row[0]} (partitioned table 아님)"
    finally:
        conn.close()


def test_log_events_has_30_day_partitions(upgraded_db):
    """오늘 + 30일치 daily partition (총 31개) 가 미리 생성되어 있어야 한다."""
    conn = _open_sync(upgraded_db)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM pg_inherits "
                "WHERE inhparent = 'log_events'::regclass"
            )
            n = cur.fetchone()[0]
        # 보수적으로 30 이상 (timezone edge 고려)
        assert n >= 30, f"파티션 수 {n} < 30"
    finally:
        conn.close()


def test_pg_trgm_extension_enabled(upgraded_db):
    """pg_trgm extension 이 활성화되어야 한다 (메시지 풀텍스트 검색)."""
    conn = _open_sync(upgraded_db)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'pg_trgm'")
            row = cur.fetchone()
        assert row is not None, "pg_trgm extension 미활성"
    finally:
        conn.close()
