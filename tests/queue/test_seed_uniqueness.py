from fluka.queue.core import fluka
from fluka.queue.core.config import SubmissionConfig
from fluka.queue import service


def test_submit_jobs_allocates_unique_seeds(tmp_path, monkeypatch):
    captured_seeds = []

    real_generate = fluka.generate_input

    def spy_generate(base, i, job_dir, nprim=None, seed=None):
        captured_seeds.append(seed)
        return real_generate(base, i, job_dir, nprim=nprim, seed=seed)

    # Force the allocator to hand out a colliding value first.
    seq = iter([500, 500, 600])
    monkeypatch.setattr(fluka.random, "randint", lambda a, b: next(seq))
    monkeypatch.setattr(service.fluka, "generate_input", spy_generate)

    class StubBackend:
        def generate_script(self, job_info, job_dir, args):
            return None
        def submit(self, script_path, job_info, args):
            return "ok"

    backends = {"stub": StubBackend()}

    src = tmp_path / "sim.inp"
    src.write_text("RANDOMIZ          1.  1\n")
    args = SubmissionConfig(
        backend="stub", input=str(src), njobs=2, custom_exe=None,
        output_dir=str(tmp_path / "out"), nprim=None,
    )
    service.submit_jobs(args, fluka_path="/fake/fluka", backends=backends)

    assert captured_seeds == [500, 600]
    assert len(set(captured_seeds)) == 2
