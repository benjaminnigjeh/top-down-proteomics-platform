import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.config import settings


@pytest.fixture(scope="session", autouse=True)
def temp_dirs(tmp_path_factory):
    td = tmp_path_factory.mktemp("data")
    settings.UPLOAD_DIR = td / "uploads"
    settings.JOB_DIR = td / "jobs"
    settings.UPLOAD_DIR.mkdir(parents=True)
    settings.JOB_DIR.mkdir(parents=True)


@pytest.fixture(scope="function")
def db_engine(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSession()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_mzml_bytes() -> bytes:
    # Minimal valid mzML structure for testing
    return b"""<?xml version="1.0" encoding="utf-8"?>
<indexedmzML xmlns="http://psi.hupo.org/ms/mzml">
  <mzML>
    <run>
      <spectrumList count="1" defaultDataProcessingRef="dp">
        <spectrum index="0" id="scan=1" defaultArrayLength="5">
          <binaryDataArrayList count="2">
            <binaryDataArray>
              <binary>AAAAAAAAAAAAAAAAAA==</binary>
            </binaryDataArray>
            <binaryDataArray>
              <binary>AAAAAAAAAAAAAAAAAA==</binary>
            </binaryDataArray>
          </binaryDataArrayList>
        </spectrum>
      </spectrumList>
    </run>
  </mzML>
</indexedmzML>"""


@pytest.fixture
def sample_fasta_bytes() -> bytes:
    return b""">P62988 Ubiquitin
MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG
>P68871 Hemoglobin HBB
MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSD
"""
