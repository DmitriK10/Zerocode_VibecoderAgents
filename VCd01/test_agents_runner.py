# test_agents_runner.py
import unittest
from unittest.mock import patch, MagicMock
import agents_runner
from crewai import LLM

class TestAgentsRunner(unittest.TestCase):
    
    def setUp(self):
        # Создаём тестовый LLM-объект, который будет проходить валидацию
        self.test_llm = LLM(
            model="test-model",
            base_url="http://test",
            api_key="test",
            timeout=10
        )

    @patch('agents_runner.get_llm')
    @patch('agents_runner.Crew')
    def test_run_ai_history_calls_crew_kickoff(self, mock_crew_class, mock_get_llm):
        # Подставляем реальный LLM вместо мока
        mock_get_llm.return_value = self.test_llm
        
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "Результат"
        mock_crew_class.return_value = mock_crew_instance

        result = agents_runner.run_ai_history(enable_fact_check=False)

        mock_crew_class.assert_called_once()
        mock_crew_instance.kickoff.assert_called_once()
        self.assertEqual(result, "Результат")

    @patch('agents_runner.get_llm')
    @patch('agents_runner.Crew')
    def test_run_ai_history_with_factcheck(self, mock_crew_class, mock_get_llm):
        mock_get_llm.return_value = self.test_llm
        
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "Результат с фактчекером"
        mock_crew_class.return_value = mock_crew_instance

        result = agents_runner.run_ai_history(enable_fact_check=True)

        mock_crew_class.assert_called_once()
        mock_crew_instance.kickoff.assert_called_once()
        self.assertEqual(result, "Результат с фактчекером")

    @patch('agents_runner.check_url_availability', return_value=True)
    @patch('agents_runner.get_llm')
    @patch('agents_runner.Crew')
    def test_run_seo_analysis(self, mock_crew_class, mock_get_llm, mock_check_url):
        mock_get_llm.return_value = self.test_llm
        
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "SEO-результат"
        mock_crew_class.return_value = mock_crew_instance

        result = agents_runner.run_seo_analysis("https://example.com")

        mock_check_url.assert_called_with("https://example.com")
        mock_crew_class.assert_called_once()
        mock_crew_instance.kickoff.assert_called_once()
        self.assertEqual(result, "SEO-результат")

    @patch('agents_runner.check_url_availability', return_value=False)
    def test_run_seo_analysis_url_unavailable(self, mock_check_url):
        result = agents_runner.run_seo_analysis("https://unavailable.com")
        self.assertIn("недоступен", result)

    @patch('agents_runner.get_llm')
    @patch('agents_runner.Crew')
    def test_run_custom_task(self, mock_crew_class, mock_get_llm):
        mock_get_llm.return_value = self.test_llm
        
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "Ответ на задачу"
        mock_crew_class.return_value = mock_crew_instance

        result = agents_runner.run_custom_task("Сравни технологии")

        mock_crew_class.assert_called_once()
        mock_crew_instance.kickoff.assert_called_once()
        self.assertEqual(result, "Ответ на задачу")

if __name__ == '__main__':
    unittest.main()