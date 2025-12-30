import unittest

from fastapi.testclient import TestClient
from mockito import ANY, unstub, when
from challenge import app
import challenge.api as api


class TestBatchPipeline(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        unstub()

    def test_should_get_predict(self):
        data = {
            "flights": [{"OPERA": "Aerolineas Argentinas", "TIPOVUELO": "N", "MES": 3}]
        }
        when(api).load_environment_variables().thenReturn(
            api.EnvironmentVariables(
                local_model_path="logreg.joblib",
                gcp_bucket_name="bucket",
                gcp_model_path="path",
            )
        )
        when(api).download_model_from_gcp(ANY).thenReturn(None)
        when(api.DelayModel).load(ANY).thenReturn(None)
        when(api.DelayModel).predict(ANY).thenReturn([0])
        response = self.client.post("/predict", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"predict": [0]})

    def test_should_failed_unkown_column_1(self):
        data = {
            "flights": [{"OPERA": "Aerolineas Argentinas", "TIPOVUELO": "N", "MES": 13}]
        }
        when(api).load_environment_variables().thenReturn(
            api.EnvironmentVariables(
                local_model_path="logreg.joblib",
                gcp_bucket_name="bucket",
                gcp_model_path="path",
            )
        )
        when(api).download_model_from_gcp(ANY).thenReturn(None)
        when(api.DelayModel).load(ANY).thenReturn(None)
        response = self.client.post("/predict", json=data)
        self.assertEqual(response.status_code, 400)

    def test_should_failed_unkown_column_2(self):
        data = {
            "flights": [{"OPERA": "Aerolineas Argentinas", "TIPOVUELO": "O", "MES": 13}]
        }
        when(api).load_environment_variables().thenReturn(
            api.EnvironmentVariables(
                local_model_path="logreg.joblib",
                gcp_bucket_name="bucket",
                gcp_model_path="path",
            )
        )
        when(api).download_model_from_gcp(ANY).thenReturn(None)
        when(api.DelayModel).load(ANY).thenReturn(None)
        response = self.client.post("/predict", json=data)
        self.assertEqual(response.status_code, 400)

    def test_should_failed_unkown_column_3(self):
        data = {"flights": [{"OPERA": "Argentinas", "TIPOVUELO": "O", "MES": 13}]}
        when(api).load_environment_variables().thenReturn(
            api.EnvironmentVariables(
                local_model_path="logreg.joblib",
                gcp_bucket_name="bucket",
                gcp_model_path="path",
            )
        )
        when(api).download_model_from_gcp(ANY).thenReturn(None)
        when(api.DelayModel).load(ANY).thenReturn(None)
        response = self.client.post("/predict", json=data)
        self.assertEqual(response.status_code, 400)
