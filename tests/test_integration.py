"""Integration tests for blk-unblk.

These tests verify the core functionality without modifying the real /etc/hosts.
All tests use temporary files with standard permissions - no root required.
"""

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from blkunblk.hosts import block_all, unblock_all, unblock_domains
from blkunblk.recents import RecentsError, list_recents, update_recents
from blkunblk.eventlog import log_block, log_unblock
from blkunblk.lockdown import (
    LockdownError,
    clear_lockdown,
    format_remaining,
    get_lockdown_end,
    get_lockdown_remaining,
    is_locked,
    set_lockdown,
)


SAMPLE_HOSTS = """\
127.0.0.1 localhost
255.255.255.255 broadcasthost
::1 localhost

# Blocked sites
0.0.0.0 facebook.com # BLOCKME
0.0.0.0 twitter.com # BLOCKME
0.0.0.0 reddit.com # BLOCKME

# Never unblock this one
0.0.0.0 important.com # NEVERBLOCK
"""


class TestBlockAll(unittest.TestCase):
    """Tests for block_all() function."""

    def test_block_all_uncomments_blockme_lines(self):
        """Verify block_all() uncomments all BLOCKME lines."""
        # Start with some commented-out lines
        initial = """\
127.0.0.1 localhost
#0.0.0.0 facebook.com # BLOCKME
# 0.0.0.0 twitter.com # BLOCKME
0.0.0.0 reddit.com # BLOCKME
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hosts', delete=False) as f:
            f.write(initial)
            temp_path = Path(f.name)

        try:
            block_all(temp_path)
            result = temp_path.read_text()

            # All BLOCKME lines should be uncommented (active)
            self.assertIn("0.0.0.0 facebook.com # BLOCKME", result)
            self.assertIn("0.0.0.0 twitter.com # BLOCKME", result)
            self.assertIn("0.0.0.0 reddit.com # BLOCKME", result)
            # localhost should remain unchanged
            self.assertIn("127.0.0.1 localhost", result)
        finally:
            temp_path.unlink()

    def test_block_all_preserves_neverblock(self):
        """Verify NEVERBLOCK lines are never modified by block_all."""
        initial = """\
0.0.0.0 important.com # NEVERBLOCK
#0.0.0.0 facebook.com # BLOCKME
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hosts', delete=False) as f:
            f.write(initial)
            temp_path = Path(f.name)

        try:
            block_all(temp_path)
            result = temp_path.read_text()

            # NEVERBLOCK line should be unchanged
            self.assertIn("0.0.0.0 important.com # NEVERBLOCK", result)
            # BLOCKME line should be uncommented
            self.assertIn("0.0.0.0 facebook.com # BLOCKME", result)
        finally:
            temp_path.unlink()


class TestUnblockAll(unittest.TestCase):
    """Tests for unblock_all() function."""

    def test_unblock_all_comments_blockme_lines(self):
        """Verify unblock_all() comments all BLOCKME lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hosts', delete=False) as f:
            f.write(SAMPLE_HOSTS)
            temp_path = Path(f.name)

        try:
            unblock_all(temp_path)
            result = temp_path.read_text()

            # All BLOCKME lines should be commented
            self.assertIn("# 0.0.0.0 facebook.com # BLOCKME", result)
            self.assertIn("# 0.0.0.0 twitter.com # BLOCKME", result)
            self.assertIn("# 0.0.0.0 reddit.com # BLOCKME", result)
            # localhost should remain unchanged
            self.assertIn("127.0.0.1 localhost", result)
        finally:
            temp_path.unlink()

    def test_unblock_all_preserves_neverblock(self):
        """Verify NEVERBLOCK lines are never modified by unblock_all."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hosts', delete=False) as f:
            f.write(SAMPLE_HOSTS)
            temp_path = Path(f.name)

        try:
            unblock_all(temp_path)
            result = temp_path.read_text()

            # NEVERBLOCK line should NOT be commented
            self.assertIn("0.0.0.0 important.com # NEVERBLOCK", result)
            self.assertNotIn("# 0.0.0.0 important.com # NEVERBLOCK", result)
        finally:
            temp_path.unlink()


class TestUnblockSpecific(unittest.TestCase):
    """Tests for unblock_domains() function."""

    def test_unblock_specific_domains(self):
        """Verify unblock_domains() only comments matching domains."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hosts', delete=False) as f:
            f.write(SAMPLE_HOSTS)
            temp_path = Path(f.name)

        try:
            unblock_domains(["facebook.com"], temp_path)
            result = temp_path.read_text()

            # Only facebook.com should be commented
            self.assertIn("# 0.0.0.0 facebook.com # BLOCKME", result)
            # Other BLOCKME sites should remain active
            self.assertIn("0.0.0.0 twitter.com # BLOCKME", result)
            self.assertIn("0.0.0.0 reddit.com # BLOCKME", result)
        finally:
            temp_path.unlink()

    def test_unblock_multiple_domains(self):
        """Verify unblock_domains() handles multiple domains."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hosts', delete=False) as f:
            f.write(SAMPLE_HOSTS)
            temp_path = Path(f.name)

        try:
            unblock_domains(["facebook.com", "reddit.com"], temp_path)
            result = temp_path.read_text()

            # Both should be commented
            self.assertIn("# 0.0.0.0 facebook.com # BLOCKME", result)
            self.assertIn("# 0.0.0.0 reddit.com # BLOCKME", result)
            # twitter should remain active
            self.assertIn("0.0.0.0 twitter.com # BLOCKME", result)
        finally:
            temp_path.unlink()

    def test_unblock_specific_preserves_neverblock(self):
        """Verify NEVERBLOCK is preserved even if domain matches."""
        initial = """\
0.0.0.0 important.com # NEVERBLOCK
0.0.0.0 facebook.com # BLOCKME
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hosts', delete=False) as f:
            f.write(initial)
            temp_path = Path(f.name)

        try:
            # Try to unblock important.com (which has NEVERBLOCK)
            unblock_domains(["important.com"], temp_path)
            result = temp_path.read_text()

            # NEVERBLOCK should NOT be commented
            self.assertIn("0.0.0.0 important.com # NEVERBLOCK", result)
            self.assertNotIn("# 0.0.0.0 important.com", result)
        finally:
            temp_path.unlink()


class TestRecents(unittest.TestCase):
    """Tests for recents functionality."""

    def test_update_recents(self):
        """Verify recents file is updated correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            focus_dir = Path(temp_dir) / ".focus"
            recents_file = focus_dir / "recents"

            update_recents(["facebook.com", "twitter.com"], focus_dir, recents_file)

            result = list_recents(focus_dir, recents_file)
            # First domain in input ends up first (most recent)
            self.assertEqual(result, ["facebook.com", "twitter.com"])

    def test_recents_limit(self):
        """Verify recents respects RECENTS_MAX limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            focus_dir = Path(temp_dir) / ".focus"
            recents_file = focus_dir / "recents"

            # Add more than RECENTS_MAX domains
            update_recents(["a.com", "b.com", "c.com", "d.com", "e.com"], focus_dir, recents_file)

            result = list_recents(focus_dir, recents_file)
            # Should only keep RECENTS_MAX (3) most recent
            # First domains in input are considered most recent
            self.assertEqual(len(result), 3)
            self.assertEqual(result, ["a.com", "b.com", "c.com"])

    def test_recents_deduplication(self):
        """Verify duplicate domains are moved to front."""
        with tempfile.TemporaryDirectory() as temp_dir:
            focus_dir = Path(temp_dir) / ".focus"
            recents_file = focus_dir / "recents"

            update_recents(["a.com", "b.com"], focus_dir, recents_file)
            update_recents(["a.com"], focus_dir, recents_file)

            result = list_recents(focus_dir, recents_file)
            # a.com should be at front (most recent)
            self.assertEqual(result[0], "a.com")

    def test_recents_error_on_permission_issue(self):
        """Verify RecentsError is raised on permission issues."""
        # Try to write to a path we can't access
        with tempfile.TemporaryDirectory() as temp_dir:
            focus_dir = Path(temp_dir) / ".focus"
            focus_dir.mkdir()
            recents_file = focus_dir / "recents"
            recents_file.touch()
            # Make file read-only
            recents_file.chmod(0o444)

            try:
                with self.assertRaises(RecentsError):
                    update_recents(["test.com"], focus_dir, recents_file)
            finally:
                # Restore permissions for cleanup
                recents_file.chmod(0o644)


class TestEventLog(unittest.TestCase):
    """Tests for event logging."""

    def test_log_block(self):
        """Verify block events are logged correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            temp_log = Path(f.name)

        try:
            log_block(temp_log)
            content = temp_log.read_text()

            self.assertIn("BLOCK", content)
            # Should have timestamp format
            self.assertRegex(content, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        finally:
            temp_log.unlink()

    def test_log_unblock(self):
        """Verify unblock events are logged correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            temp_log = Path(f.name)

        try:
            log_unblock(25, "testing", log_file=temp_log)
            content = temp_log.read_text()

            self.assertIn("UNBLOCK", content)
            self.assertIn("Duration: 25 minutes", content)
            self.assertIn("Reason: testing", content)
        finally:
            temp_log.unlink()

    def test_log_unblock_with_domains(self):
        """Verify unblock events with specific domains are logged correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            temp_log = Path(f.name)

        try:
            log_unblock(10, "quick check", ["facebook.com", "twitter.com"], temp_log)
            content = temp_log.read_text()

            self.assertIn("UNBLOCK", content)
            self.assertIn("Specific: facebook.com, twitter.com", content)
        finally:
            temp_log.unlink()


class TestLockdown(unittest.TestCase):
    """Tests for lockdown functionality."""

    def test_set_lockdown(self):
        """Verify lockdown can be set."""
        with tempfile.TemporaryDirectory() as temp_dir:
            focus_dir = Path(temp_dir) / ".focus"
            lockdown_file = focus_dir / "lockdown"

            end_time = set_lockdown(1.0, lockdown_file, focus_dir)

            self.assertTrue(lockdown_file.exists())
            self.assertTrue(is_locked(lockdown_file))
            # End time should be about 1 hour from now
            expected = datetime.now() + timedelta(hours=1)
            self.assertAlmostEqual(
                end_time.timestamp(), expected.timestamp(), delta=5
            )

    def test_lockdown_capped_at_midnight(self):
        """Verify lockdown is capped at midnight."""
        with tempfile.TemporaryDirectory() as temp_dir:
            focus_dir = Path(temp_dir) / ".focus"
            lockdown_file = focus_dir / "lockdown"

            # Request 100 hours (way past midnight)
            end_time = set_lockdown(100.0, lockdown_file, focus_dir)

            # Should be capped at midnight today
            midnight = datetime.now().replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            self.assertLessEqual(end_time, midnight)

    def test_is_locked(self):
        """Verify is_locked returns correct state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            focus_dir = Path(temp_dir) / ".focus"
            lockdown_file = focus_dir / "lockdown"

            # Not locked initially
            self.assertFalse(is_locked(lockdown_file))

            # Set lockdown
            set_lockdown(1.0, lockdown_file, focus_dir)
            self.assertTrue(is_locked(lockdown_file))

            # Clear lockdown
            clear_lockdown(lockdown_file)
            self.assertFalse(is_locked(lockdown_file))

    def test_expired_lockdown(self):
        """Verify expired lockdown is not active."""
        with tempfile.TemporaryDirectory() as temp_dir:
            focus_dir = Path(temp_dir) / ".focus"
            focus_dir.mkdir(parents=True)
            lockdown_file = focus_dir / "lockdown"

            # Write an expired timestamp
            past = datetime.now() - timedelta(hours=1)
            lockdown_file.write_text(past.isoformat())

            self.assertFalse(is_locked(lockdown_file))
            self.assertIsNone(get_lockdown_end(lockdown_file))

    def test_get_lockdown_remaining(self):
        """Verify remaining time calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            focus_dir = Path(temp_dir) / ".focus"
            lockdown_file = focus_dir / "lockdown"

            set_lockdown(1.0, lockdown_file, focus_dir)
            remaining = get_lockdown_remaining(lockdown_file)

            self.assertIsNotNone(remaining)
            # Should be close to 1 hour
            assert remaining is not None  # for type checker
            self.assertGreater(remaining.total_seconds(), 3500)  # > 58 min
            self.assertLess(remaining.total_seconds(), 3700)  # < 62 min

    def test_format_remaining(self):
        """Verify time formatting."""
        self.assertEqual(format_remaining(timedelta(hours=2, minutes=30)), "2h 30m")
        self.assertEqual(format_remaining(timedelta(minutes=45, seconds=30)), "45m 30s")
        self.assertEqual(format_remaining(timedelta(seconds=30)), "30s")

    def test_lockdown_error_on_invalid_hours(self):
        """Verify error on invalid hours."""
        with tempfile.TemporaryDirectory() as temp_dir:
            focus_dir = Path(temp_dir) / ".focus"
            lockdown_file = focus_dir / "lockdown"

            with self.assertRaises(LockdownError):
                set_lockdown(0, lockdown_file, focus_dir)

            with self.assertRaises(LockdownError):
                set_lockdown(-1, lockdown_file, focus_dir)


if __name__ == "__main__":
    unittest.main()
