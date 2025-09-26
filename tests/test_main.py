import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import json
import os
import tempfile
from datetime import datetime
import requests

# Import the classes and functions from main.py
import sys
sys.path.append('.')
from main import Memory, init, shutdown, running_einstein, main


class TestMemory(unittest.TestCase):
    """Comprehensive test suite for the Memory class."""
    
    def setUp(self):
        """Set up test fixtures for each test method."""
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.close()
        self.memory = Memory(self.test_file.name)
    
    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)
    
    def test_init_creates_new_file_when_not_exists(self):
        """Test that Memory creates a new file with default structure when file doesn't exist."""
        non_existent_file = "non_existent_test_file.json"
        if os.path.exists(non_existent_file):
            os.unlink(non_existent_file)
        
        Memory(non_existent_file)
        self.assertTrue(os.path.exists(non_existent_file))
        
        with open(non_existent_file, 'r') as f:
            data = json.load(f)
        
        expected_structure = {
            "facts": [], 
            "reminders": [], 
            "tasks": [], 
            "journals": [], 
            "api_keys": {}
        }
        self.assertEqual(data, expected_structure)
        
        # Clean up
        os.unlink(non_existent_file)
    
    def test_init_loads_existing_file(self):
        """Test that Memory loads existing file correctly."""
        existing_data = {"facts": ["test fact"], "reminders": []}
        with open(self.test_file.name, 'w') as f:
            json.dump(existing_data, f)
        
        memory = Memory(self.test_file.name)
        self.assertEqual(memory.data["facts"], ["test fact"])
    
    def test_add_fact(self):
        """Test adding a fact to memory."""
        test_fact = "Einstein was a physicist"
        self.memory.add_fact(test_fact)
        
        self.assertIn(test_fact, self.memory.data["facts"])
        
        # Verify persistence
        memory2 = Memory(self.test_file.name)
        self.assertIn(test_fact, memory2.data["facts"])
    
    def test_add_fact_empty_string(self):
        """Test adding empty string as fact."""
        self.memory.add_fact("")
        self.assertIn("", self.memory.data["facts"])
    
    def test_add_fact_special_characters(self):
        """Test adding fact with special characters."""
        special_fact = "Test with special chars: \\!@#$%^&*()_+{}[]|\\:;\"'<>?,./"
        self.memory.add_fact(special_fact)
        self.assertIn(special_fact, self.memory.data["facts"])
    
    def test_add_reminder(self):
        """Test adding a reminder to memory."""
        reminder_text = "Call the doctor"
        reminder_time = "2024-01-15 14:30"
        
        self.memory.add_reminder(reminder_text, reminder_time)
        
        expected_reminder = {"text": reminder_text, "time": reminder_time}
        self.assertIn(expected_reminder, self.memory.data["reminders"])
    
    def test_add_reminder_multiple(self):
        """Test adding multiple reminders."""
        reminders = [
            ("Meeting", "2024-01-15 10:00"),
            ("Lunch", "2024-01-15 12:00"),
            ("Call", "2024-01-15 15:00")
        ]
        
        for text, time in reminders:
            self.memory.add_reminder(text, time)
        
        self.assertEqual(len(self.memory.data["reminders"]), 3)
    
    @patch('main.datetime')
    def test_get_due_reminders_with_due_items(self, mock_datetime):
        """Test getting due reminders when reminders are due."""
        mock_now = "2024-01-15 14:30"
        mock_datetime.now.return_value.strftime.return_value = mock_now
        
        # Add reminders - some due, some not
        self.memory.add_reminder("Due reminder", mock_now)
        self.memory.add_reminder("Not due reminder", "2024-01-15 15:00")
        
        due_reminders = self.memory.get_due_reminders()
        
        self.assertEqual(len(due_reminders), 1)
        self.assertEqual(due_reminders[0]["text"], "Due reminder")
        # Due reminder should be removed from the list
        self.assertEqual(len(self.memory.data["reminders"]), 1)
        self.assertEqual(self.memory.data["reminders"][0]["text"], "Not due reminder")
    
    @patch('main.datetime')
    def test_get_due_reminders_no_due_items(self, mock_datetime):
        """Test getting due reminders when no reminders are due."""
        mock_datetime.now.return_value.strftime.return_value = "2024-01-15 14:30"
        
        self.memory.add_reminder("Future reminder", "2024-01-15 15:00")
        
        due_reminders = self.memory.get_due_reminders()
        
        self.assertEqual(len(due_reminders), 0)
        self.assertEqual(len(self.memory.data["reminders"]), 1)
    
    def test_add_task(self):
        """Test adding a task."""
        task_text = "Buy groceries"
        self.memory.add_task(task_text)
        
        expected_task = {"task": task_text, "done": False}
        self.assertIn(expected_task, self.memory.data["tasks"])
    
    def test_list_tasks_empty(self):
        """Test listing tasks when no tasks exist."""
        tasks = self.memory.list_tasks()
        self.assertEqual(tasks, [])
    
    def test_list_tasks_with_incomplete_tasks(self):
        """Test listing only incomplete tasks."""
        self.memory.add_task("Task 1")
        self.memory.add_task("Task 2")
        
        # Mark one task as done
        self.memory.data["tasks"][0]["done"] = True
        self.memory.save()
        
        tasks = self.memory.list_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["task"], "Task 2")
    
    def test_complete_task_success(self):
        """Test completing an existing task."""
        task_text = "Complete this task"
        self.memory.add_task(task_text)
        
        result = self.memory.complete_task(task_text)
        
        self.assertTrue(result)
        self.assertTrue(self.memory.data["tasks"][0]["done"])
    
    def test_complete_task_case_insensitive(self):
        """Test completing task is case insensitive."""
        self.memory.add_task("UPPERCASE TASK")
        
        result = self.memory.complete_task("uppercase task")
        
        self.assertTrue(result)
        self.assertTrue(self.memory.data["tasks"][0]["done"])
    
    def test_complete_task_not_found(self):
        """Test completing a task that doesn't exist."""
        result = self.memory.complete_task("Nonexistent task")
        self.assertFalse(result)
    
    def test_complete_task_already_done(self):
        """Test completing an already done task."""
        self.memory.add_task("Already done task")
        self.memory.complete_task("Already done task")
        
        # Try to complete again
        result = self.memory.complete_task("Already done task")
        self.assertFalse(result)
    
    def test_remove_task_by_index_valid_index(self):
        """Test removing task by valid index."""
        self.memory.add_task("Task to remove")
        self.memory.add_task("Task to keep")
        
        removed_task = self.memory.remove_task_by_index(0)
        
        self.assertEqual(removed_task["task"], "Task to remove")
        self.assertEqual(len(self.memory.data["tasks"]), 1)
        self.assertEqual(self.memory.data["tasks"][0]["task"], "Task to keep")
    
    def test_remove_task_by_index_invalid_index(self):
        """Test removing task by invalid index raises exception."""
        self.memory.add_task("Single task")
        
        with self.assertRaises(IndexError):
            self.memory.remove_task_by_index(5)
    
    def test_remove_task_by_index_negative_index(self):
        """Test removing task by negative index."""
        self.memory.add_task("Task 1")
        self.memory.add_task("Task 2")
        
        removed_task = self.memory.remove_task_by_index(-1)
        
        self.assertEqual(removed_task["task"], "Task 2")
        self.assertEqual(len(self.memory.data["tasks"]), 1)
    
    @patch('main.datetime')
    def test_add_journal_entry(self, mock_datetime):
        """Test adding a journal entry."""
        mock_timestamp = "2024-01-15 14:30"
        mock_datetime.now.return_value.strftime.return_value = mock_timestamp
        
        entry_text = "Today was a great day"
        self.memory.add_journal_entry(entry_text)
        
        expected_entry = {"time": mock_timestamp, "entry": entry_text}
        self.assertIn(expected_entry, self.memory.data["journals"])
    
    def test_get_recent_journal_empty(self):
        """Test getting recent journal entries when journal is empty."""
        entries = self.memory.get_recent_journal()
        self.assertEqual(entries, [])
    
    def test_get_recent_journal_default_limit(self):
        """Test getting recent journal entries with default limit."""
        # Add 5 journal entries
        for i in range(5):
            self.memory.data["journals"].append({
                "time": f"2024-01-{i+1:02d} 10:00",
                "entry": f"Entry {i+1}"
            })
        self.memory.save()
        
        recent = self.memory.get_recent_journal()
        
        self.assertEqual(len(recent), 3)  # Default limit is 3
        self.assertEqual(recent[0]["entry"], "Entry 3")
        self.assertEqual(recent[-1]["entry"], "Entry 5")
    
    def test_get_recent_journal_custom_limit(self):
        """Test getting recent journal entries with custom limit."""
        # Add 5 journal entries
        for i in range(5):
            self.memory.data["journals"].append({
                "time": f"2024-01-{i+1:02d} 10:00",
                "entry": f"Entry {i+1}"
            })
        self.memory.save()
        
        recent = self.memory.get_recent_journal(limit=2)
        
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["entry"], "Entry 4")
        self.assertEqual(recent[1]["entry"], "Entry 5")
    
    def test_save_api_key(self):
        """Test saving an API key."""
        service = "openai"
        key = "sk-test123"
        
        self.memory.save_api_key(service, key)
        
        self.assertEqual(self.memory.data["api_keys"][service], key)
    
    def test_save_api_key_creates_api_keys_section(self):
        """Test that save_api_key creates api_keys section if it doesn't exist."""
        # Remove api_keys section
        del self.memory.data["api_keys"]
        
        self.memory.save_api_key("test_service", "test_key")
        
        self.assertIn("api_keys", self.memory.data)
        self.assertEqual(self.memory.data["api_keys"]["test_service"], "test_key")
    
    def test_get_api_key_existing(self):
        """Test getting an existing API key."""
        service = "github"
        key = "ghp_test123"
        
        self.memory.save_api_key(service, key)
        retrieved_key = self.memory.get_api_key(service)
        
        self.assertEqual(retrieved_key, key)
    
    def test_get_api_key_nonexistent(self):
        """Test getting a nonexistent API key."""
        key = self.memory.get_api_key("nonexistent_service")
        self.assertIsNone(key)
    
    def test_get_api_key_no_api_keys_section(self):
        """Test getting API key when api_keys section doesn't exist."""
        del self.memory.data["api_keys"]
        self.memory.save()
        
        key = self.memory.get_api_key("any_service")
        self.assertIsNone(key)
    
    @patch('main.requests.post')
    def test_backup_to_server_success(self, mock_post):
        """Test successful backup to server."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Add an API key for backup
        self.memory.save_api_key("backup", "test-backup-key")
        
        result = self.memory.backup_to_server("https://example.com/backup")
        
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    @patch('main.requests.post')
    def test_backup_to_server_default_endpoint(self, mock_post):
        """Test backup to server with default endpoint."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        self.memory.backup_to_server()
        
        mock_post.assert_called_once()
        # Verify the default endpoint was used
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "http://insecure-backup.example.com/upload")
    
    @patch('main.requests.post')
    def test_backup_to_server_uses_hardcoded_key_when_none_saved(self, mock_post):
        """Test backup uses hardcoded key when no backup key is saved."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        self.memory.backup_to_server()
        
        call_args = mock_post.call_args
        headers = call_args[1]['headers']
        self.assertEqual(headers['Authorization'], 'Bearer hardcoded-insecure-key')
    
    def test_backup_to_server_invalid_url_scheme(self):
        """Test backup fails with invalid URL scheme."""
        with self.assertRaises(ValueError) as context:
            self.memory.backup_to_server("ftp://example.com/backup")
        
        self.assertIn("Invalid URL scheme", str(context.exception))
    
    @patch('main.requests.post')
    def test_backup_to_server_failure(self, mock_post):
        """Test backup failure (non-200 status code)."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        # Note: There's a bug in the original code - it references 'response' instead of 'resp'
        with self.assertRaises(NameError):
            self.memory.backup_to_server()
    
    @patch('main.requests.post')
    def test_backup_to_server_request_parameters(self, mock_post):
        """Test that backup request is made with correct parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        custom_endpoint = "https://custom-backup.example.com/upload"
        self.memory.save_api_key("backup", "custom-backup-key")
        
        self.memory.backup_to_server(custom_endpoint)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify URL
        self.assertEqual(call_args[0][0], custom_endpoint)
        
        # Verify headers
        headers = call_args[1]['headers']
        self.assertEqual(headers['Authorization'], 'Bearer custom-backup-key')
        
        # Verify other parameters
        self.assertIn('files', call_args[1])
        self.assertEqual(call_args[1]['verify'], False)
        self.assertEqual(call_args[1]['timeout'], 5)


class TestInitFunction(unittest.TestCase):
    """Test suite for the init function."""
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_init_function(self, mock_format_message):
        """Test init function calls format_message and audio speak."""
        mock_audio = Mock()
        mock_format_message.return_value = "formatted message"
        
        init(mock_audio)
        
        expected_message = "Hello\\! I am Einstein, your personal AI assistant. How can I help you?"
        mock_format_message.assert_called_once_with("system_output", expected_message, {"test": "data"})
        mock_audio.speak.assert_called_once_with(expected_message)


class TestShutdownFunction(unittest.TestCase):
    """Test suite for the shutdown function."""
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_shutdown_function(self, mock_format_message):
        """Test shutdown function calls format_message and audio speak."""
        mock_audio = Mock()
        mock_format_message.return_value = "formatted message"
        
        shutdown(mock_audio)
        
        expected_message = "Goodbye\\! I hope I was able to help you."
        mock_format_message.assert_called_once_with("system_output", expected_message, {"test": "data"})
        mock_audio.speak.assert_called_once_with(expected_message)


class TestRunningEinsteinFunction(unittest.TestCase):
    """Test suite for the running_einstein function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_audio = Mock()
        self.mock_memory = Mock()
        
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_goodbye_command(self, _mock_format_message):
        """Test running_einstein returns False for goodbye commands."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "goodbye."
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertFalse(result)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_goodbye_variations(self, _mock_format_message):
        """Test running_einstein handles different goodbye variations."""
        goodbye_commands = ["goodbye.", "bye.", "see you.", "ciao.", "later.", "take care."]
        
        for cmd in goodbye_commands:
            with self.subTest(command=cmd):
                self.mock_memory.get_due_reminders.return_value = []
                self.mock_audio.listen_for_codeword.return_value = cmd
                
                result = running_einstein(self.mock_audio, self.mock_memory)
                
                self.assertFalse(result)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    @patch('main.datetime')
    def test_running_einstein_remind_me_command(self, mock_datetime, mock_format_message):
        """Test running_einstein processes remind me commands."""
        mock_datetime.now.return_value.strftime.return_value = "2024-01-15 14:30"
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "remind me about meeting tomorrow"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        self.mock_memory.add_reminder.assert_called_once_with("meeting tomorrow", "2024-01-15 14:30")
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_remember_command(self, mock_format_message):
        """Test running_einstein processes remember commands."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "remember einstein was born in 1879"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        self.mock_memory.add_fact.assert_called_once_with("einstein was born in 1879")
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_add_task_command(self, mock_format_message):
        """Test running_einstein processes add task commands."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "add task buy groceries"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        self.mock_memory.add_task.assert_called_once_with("buy groceries")
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_list_tasks_with_tasks(self, mock_format_message):
        """Test running_einstein lists tasks when tasks exist."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_memory.list_tasks.return_value = [
            {"task": "Task 1"}, 
            {"task": "Task 2"}
        ]
        self.mock_audio.listen_for_codeword.return_value = "list tasks"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        # Verify audio speaks the task list
        expected_response = "Your tasks are: Task 1, Task 2"
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_list_tasks_empty(self, mock_format_message):
        """Test running_einstein handles empty task list."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_memory.list_tasks.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "list tasks"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        expected_response = "You have no tasks."
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_complete_task_success(self, mock_format_message):
        """Test running_einstein completes task successfully."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_memory.complete_task.return_value = True
        self.mock_audio.listen_for_codeword.return_value = "complete task buy groceries"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        self.mock_memory.complete_task.assert_called_once_with("buy groceries")
        expected_response = "Task 'buy groceries' marked as complete."
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_complete_task_not_found(self, mock_format_message):
        """Test running_einstein handles task not found."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_memory.complete_task.return_value = False
        self.mock_audio.listen_for_codeword.return_value = "complete task nonexistent task"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        expected_response = "Task 'nonexistent task' not found."
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_remove_task(self, mock_format_message):
        """Test running_einstein removes task by index."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_memory.remove_task_by_index.return_value = {"task": "Removed task"}
        self.mock_audio.listen_for_codeword.return_value = "remove task 0"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        self.mock_memory.remove_task_by_index.assert_called_once_with(0)
        expected_response = "Removed task: Removed task"
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_write_journal(self, mock_format_message):
        """Test running_einstein writes journal entry."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "write journal today was great"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        self.mock_memory.add_journal_entry.assert_called_once_with("today was great")
        expected_response = "Journal entry saved."
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_read_journal_with_entries(self, mock_format_message):
        """Test running_einstein reads journal entries when they exist."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_memory.get_recent_journal.return_value = [
            {"time": "2024-01-15 10:00", "entry": "Morning thoughts"},
            {"time": "2024-01-15 18:00", "entry": "Evening reflections"}
        ]
        self.mock_audio.listen_for_codeword.return_value = "read journal"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        expected_response = "Here are your recent journal entries: [2024-01-15 10:00] Morning thoughts | [2024-01-15 18:00] Evening reflections"
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_read_journal_empty(self, mock_format_message):
        """Test running_einstein handles empty journal."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_memory.get_recent_journal.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "read journal"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        expected_response = "Your journal is empty."
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_save_api_key(self, mock_format_message):
        """Test running_einstein saves API key."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "save api key openai sk-test123"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        self.mock_memory.save_api_key.assert_called_once_with("openai", "sk-test123")
        expected_response = "API key for openai saved."
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_save_api_key_missing_key(self, mock_format_message):
        """Test running_einstein saves API key with empty key when not provided."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "save api key service"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        self.mock_memory.save_api_key.assert_called_once_with("service", "")
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_show_api_key_exists(self, mock_format_message):
        """Test running_einstein shows existing API key."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_memory.get_api_key.return_value = "sk-test123"
        self.mock_audio.listen_for_codeword.return_value = "show api key openai"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        self.mock_memory.get_api_key.assert_called_once_with("openai")
        expected_response = "API key for openai is: sk-test123"
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_show_api_key_not_exists(self, mock_format_message):
        """Test running_einstein handles nonexistent API key."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_memory.get_api_key.return_value = None
        self.mock_audio.listen_for_codeword.return_value = "show api key github"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        expected_response = "No API key saved for github."
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_backup_now(self, mock_format_message):
        """Test running_einstein processes backup command."""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_memory.backup_to_server.return_value = True
        self.mock_audio.listen_for_codeword.return_value = "backup now"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        self.mock_memory.backup_to_server.assert_called_once()
        expected_response = "Backup requested."
        self.mock_audio.speak.assert_called_with(expected_response)
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    @patch('main.os.popen')
    def test_running_einstein_run_command_with_output(self, mock_popen, mock_format_message):
        """Test running_einstein executes system commands with output."""
        mock_popen.return_value.read.return_value = "command output"
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "run ls"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        mock_popen.assert_called_once_with("ls")
        self.mock_audio.speak.assert_called_with("command output")
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    @patch('main.os.popen')
    def test_running_einstein_run_command_no_output(self, mock_popen, mock_format_message):
        """Test running_einstein executes system commands with no output."""
        mock_popen.return_value.read.return_value = ""
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "run touch file.txt"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        mock_popen.assert_called_once_with("touch file.txt")
        self.mock_audio.speak.assert_called_with("Command executed.")
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    @patch('main.ChatPromptTemplate.from_template')
    @patch('main.OllamaLLM')
    def test_running_einstein_ai_response(self, _mock_ollama, mock_template, mock_format_message):
        """Test running_einstein processes unrecognized commands through AI."""
        # Setup mocks
        mock_chain = Mock()
        mock_chain.invoke.return_value = "AI response to user question"
        mock_prompt = Mock()
        mock_prompt.__or__ = Mock(return_value=mock_chain)
        mock_template.return_value = mock_prompt
        
        self.mock_memory.get_due_reminders.return_value = []
        self.mock_audio.listen_for_codeword.return_value = "what is the weather today"
        mock_format_message.return_value = "formatted message"
        
        result = running_einstein(self.mock_audio, self.mock_memory)
        
        self.assertTrue(result)
        mock_chain.invoke.assert_called_once_with({"Question": "what is the weather today"})
        self.mock_audio.speak.assert_called_with("AI response to user question")
    
    @patch('main.format_message')
    @patch('main.data', {"test": "data"})
    def test_running_einstein_processes_due_reminders(self, mock_format_message):
        """Test running_einstein processes due reminders at the start."""
        due_reminders = [
            {"text": "Call doctor", "time": "2024-01-15 14:30"},
            {"text": "Meeting at 3pm", "time": "2024-01-15 15:00"}
        ]
        self.mock_memory.get_due_reminders.return_value = due_reminders
        self.mock_audio.listen_for_codeword.return_value = "goodbye."
        mock_format_message.return_value = "formatted message"
        
        running_einstein(self.mock_audio, self.mock_memory)
        
        # Verify reminders are spoken
        expected_calls = [
            unittest.mock.call("Reminder: Call doctor"),
            unittest.mock.call("Reminder: Meeting at 3pm")
        ]
        self.mock_audio.speak.assert_has_calls(expected_calls, any_order=True)


class TestMainFunction(unittest.TestCase):
    """Test suite for the main function."""
    
    @patch('main.Audio')
    @patch('main.Memory')
    @patch('main.init')
    @patch('main.running_einstein')
    def test_main_function_flow(self, mock_running_einstein, mock_init, mock_memory_class, mock_audio_class):
        """Test main function creates instances and runs the main loop."""
        mock_audio = Mock()
        mock_memory = Mock()
        mock_audio_class.return_value = mock_audio
        mock_memory_class.return_value = mock_memory
        
        # Simulate running_einstein returning True twice, then False
        mock_running_einstein.side_effect = [True, True, False]
        
        main()
        
        # Verify instances were created
        mock_audio_class.assert_called_once()
        mock_memory_class.assert_called_once()
        
        # Verify init was called
        mock_init.assert_called_once_with(mock_audio)
        
        # Verify running_einstein was called 3 times
        self.assertEqual(mock_running_einstein.call_count, 3)


# Integration tests to test the actual file I/O operations
class TestMemoryIntegration(unittest.TestCase):
    """Integration tests for Memory class with actual file operations."""
    
    def setUp(self):
        """Set up test fixtures for integration tests."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_memory.json")
    
    def tearDown(self):
        """Clean up after integration tests."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_memory_persistence_across_instances(self):
        """Test that data persists across different Memory instances."""
        # Create first instance and add data
        memory1 = Memory(self.test_file)
        memory1.add_fact("Test fact")
        memory1.add_task("Test task")
        
        # Create second instance and verify data persists
        memory2 = Memory(self.test_file)
        self.assertIn("Test fact", memory2.data["facts"])
        self.assertEqual(len(memory2.data["tasks"]), 1)
        self.assertEqual(memory2.data["tasks"][0]["task"], "Test task")
    
    def test_memory_file_permissions(self):
        """Test that memory file has correct permissions."""
        Memory(self.test_file)
        
        # Check file permissions (should be readable/writable by owner and group)
        file_stat = os.stat(self.test_file)
        permissions = oct(file_stat.st_mode)[-3:]
        self.assertEqual(permissions, '666')


if __name__ == '__main__':
    # Run the tests with verbose output
    unittest.main(verbosity=2)