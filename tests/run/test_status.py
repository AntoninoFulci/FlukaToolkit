from fluka.queue.backends.base import QueueBackend, read_sentinel
from fluka.run import status as S
from fluka.run.manifest import Job


def _job(backend="ts", run_dir="/x"):
    return Job(
        combo="c1",
        run_idx=1,
        run_name="run_0001",
        run_dir=run_dir,
        backend=backend,
        job_id="1",
        input_file="s.inp",
        submitted_at="t",
        extra={},
    )


def test_read_sentinel_none_path():
    assert read_sentinel(None) is None


def test_read_sentinel_missing(tmp_path):
    assert read_sentinel(tmp_path / "nope") is None


def test_read_sentinel_ok(tmp_path):
    f = tmp_path / ".fluka_status"
    f.write_text("FLUKA_STATUS rc=0\n")
    assert read_sentinel(f) == (True, 0)


def test_read_sentinel_fail(tmp_path):
    f = tmp_path / ".fluka_status"
    f.write_text("FLUKA_STATUS rc=7\n")
    assert read_sentinel(f) == (True, 7)


class _FakeBackend(QueueBackend):
    # minimal concrete backend: only override the hooks under test
    def __init__(self, queue_state=None, sentinel=None):
        self._qs = queue_state
        self._sp = sentinel

    def _queue_state(self, job):
        return self._qs

    def _sentinel_path(self, job):
        return self._sp

    # unused abstracts:
    def add_args(self, p): ...
    def validate(self, a): ...
    def generate_script(self, j, d, a): ...
    def submit(self, s, j, a): ...
    def table_rows(self, a, fp, ff):
        return []

    def set_priority_queue(self, a, q): ...


def test_job_state_running():
    st, _ = _FakeBackend(queue_state=S.RUNNING).job_state(_job())
    assert st == S.RUNNING


def test_job_state_done(tmp_path):
    f = tmp_path / ".fluka_status"
    f.write_text("FLUKA_STATUS rc=0")
    st, _ = _FakeBackend(sentinel=f).job_state(_job())
    assert st == S.DONE


def test_job_state_fail(tmp_path):
    f = tmp_path / ".fluka_status"
    f.write_text("FLUKA_STATUS rc=2")
    st, _ = _FakeBackend(sentinel=f).job_state(_job())
    assert st == S.FAIL


def test_job_state_unknown():
    st, _ = _FakeBackend().job_state(_job())
    assert st == S.UNKNOWN


def test_queue_alive_overrides_sentinel(tmp_path):
    f = tmp_path / ".fluka_status"
    f.write_text("FLUKA_STATUS rc=0")
    st, _ = _FakeBackend(queue_state=S.PENDING, sentinel=f).job_state(_job())
    assert st == S.PENDING


def test_resolve_all_and_helpers(tmp_path):
    done = tmp_path / "d"
    done.write_text("FLUKA_STATUS rc=0")
    jobs = [_job(), _job()]
    backends = {"ts": _FakeBackend(sentinel=done)}
    sts = S.resolve_all(jobs, backends)
    assert len(sts) == 2 and all(s.state == S.DONE for s in sts)
    assert S.all_terminal(sts) is True
    assert S.summary_counts(sts)[S.DONE] == 2


def test_all_terminal_false_when_pending():
    jobs = [_job()]
    sts = S.resolve_all(jobs, {"ts": _FakeBackend(queue_state=S.PENDING)})
    assert S.all_terminal(sts) is False
