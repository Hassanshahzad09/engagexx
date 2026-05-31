from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from .models import BuyerProfile, BuyerTasks, JobsHistory, SellerBehaviorLog, SellerProfile, User
from .seller_rating import (
    DEFAULT_NEW_SELLER_RATING,
    calculate_rating_from_metrics,
    calculate_seller_rating,
    calculate_trust_score,
    clamp_decimal,
    safe_ratio,
    score_to_rating,
    update_seller_rating,
)


class SellerRatingFormulaTests(TestCase):
    def test_new_seller_with_no_history_gets_default_three_star_rating(self):
        rating_data = calculate_rating_from_metrics({})

        self.assertEqual(rating_data["rating"], DEFAULT_NEW_SELLER_RATING)
        self.assertEqual(rating_data["rating_label"], "3 Star")
        self.assertEqual(rating_data["trust_score"], 50.0)
        self.assertEqual(rating_data["final_reputation_score"], 50.0)
        self.assertEqual(rating_data["rating_source"], "new_seller_default")

    def test_zero_completed_tasks_still_gets_new_seller_default_without_division_error(self):
        rating_data = calculate_rating_from_metrics(
            {
                "AssignedTasks": 10,
                "CompletedTasks": 0,
                "ApprovedTasks": 0,
                "RejectedTasks": 0,
                "SubmittedProofs": 0,
                "AvgCompletionTime": 0,
                "TrustScore": 90,
            }
        )

        self.assertEqual(rating_data["rating"], 3)
        self.assertEqual(rating_data["success_rate"], 0.0)
        self.assertEqual(rating_data["completion_ratio"], 0.0)

    @patch("service.seller_rating.predict_rating_with_ml_model", return_value=None)
    def test_excellent_seller_metrics_can_reach_five_star_rating(self, _mock_ml):
        rating_data = calculate_rating_from_metrics(
            {
                "AssignedTasks": 100,
                "CompletedTasks": 95,
                "ApprovedTasks": 93,
                "RejectedTasks": 2,
                "SubmittedProofs": 95,
                "ProofValidityRate": 0.98,
                "AuditRetentionRate": 0.96,
                "AvgCompletionTime": 2,
                "TrustScore": 95,
            }
        )

        self.assertEqual(rating_data["rating"], 5)
        self.assertGreaterEqual(rating_data["final_reputation_score"], 85)
        self.assertEqual(rating_data["rating_source"], "formula")

    @patch("service.seller_rating.predict_rating_with_ml_model", return_value=None)
    def test_poor_seller_metrics_drop_to_one_star_rating(self, _mock_ml):
        rating_data = calculate_rating_from_metrics(
            {
                "AssignedTasks": 40,
                "CompletedTasks": 12,
                "ApprovedTasks": 3,
                "RejectedTasks": 9,
                "SubmittedProofs": 12,
                "ProofValidityRate": 0.20,
                "AuditRetentionRate": 0.10,
                "AvgCompletionTime": 18,
                "TrustScore": 12,
            }
        )

        self.assertEqual(rating_data["rating"], 1)
        self.assertLess(rating_data["final_reputation_score"], 40)

    @patch("service.seller_rating.predict_rating_with_ml_model", return_value=None)
    def test_rates_are_clamped_to_valid_ranges(self, _mock_ml):
        rating_data = calculate_rating_from_metrics(
            {
                "AssignedTasks": 10,
                "CompletedTasks": 10,
                "ApprovedTasks": 15,
                "RejectedTasks": 0,
                "SubmittedProofs": 10,
                "ProofValidityRate": 2,
                "AuditRetentionRate": 3,
                "AvgCompletionTime": Decimal("0.50"),
                "TrustScore": 150,
            }
        )

        self.assertLessEqual(rating_data["proof_validity_rate"], 1.0)
        self.assertLessEqual(rating_data["audit_retention_rate"], 1.0)
        self.assertLessEqual(rating_data["speed_score"], 1.0)
        self.assertLessEqual(rating_data["trust_score"], 100.0)
        self.assertLessEqual(rating_data["final_reputation_score"], 100.0)

    @patch("service.seller_rating.predict_rating_with_ml_model", return_value=4)
    def test_ml_model_prediction_overrides_formula_when_model_is_available(self, _mock_ml):
        rating_data = calculate_rating_from_metrics(
            {
                "AssignedTasks": 25,
                "CompletedTasks": 20,
                "ApprovedTasks": 20,
                "RejectedTasks": 0,
                "SubmittedProofs": 20,
                "ProofValidityRate": 1,
                "AuditRetentionRate": 1,
                "AvgCompletionTime": 2,
                "TrustScore": 100,
            }
        )

        self.assertEqual(rating_data["rating"], 4)
        self.assertEqual(rating_data["rating_source"], "ml_model")

    def test_score_thresholds_convert_to_correct_star_ratings(self):
        threshold_cases = [
            (85, 5),
            (84.99, 4),
            (70, 4),
            (69.99, 3),
            (55, 3),
            (54.99, 2),
            (40, 2),
            (39.99, 1),
        ]

        for score, expected_rating in threshold_cases:
            with self.subTest(score=score):
                self.assertEqual(score_to_rating(score), expected_rating)

    def test_safe_ratio_and_clamp_handle_edge_cases(self):
        self.assertEqual(safe_ratio(10, 0), Decimal("0.00"))
        self.assertEqual(safe_ratio(10, 0, default=Decimal("0.60")), Decimal("0.60"))
        self.assertEqual(clamp_decimal(-50), Decimal("0.00"))
        self.assertEqual(clamp_decimal(150), Decimal("100.00"))

    def test_trust_score_rewards_good_behavior_and_penalizes_bad_behavior(self):
        strong_trust = calculate_trust_score(
            completed_tasks=10,
            rejected_tasks=0,
            valid_proofs=10,
            invalid_proofs=0,
            audit_passed_tasks=5,
            audit_failed_tasks=0,
            unethical_reports=0,
        )
        poor_trust = calculate_trust_score(
            completed_tasks=0,
            rejected_tasks=5,
            valid_proofs=0,
            invalid_proofs=3,
            audit_passed_tasks=0,
            audit_failed_tasks=2,
            unethical_reports=2,
        )

        self.assertEqual(strong_trust, Decimal("100.00"))
        self.assertEqual(poor_trust, Decimal("0.00"))


class SellerRatingHistoryTests(TestCase):
    def setUp(self):
        self.buyer_user = User.objects.create_user(
            username="buyer1",
            email="buyer1@example.com",
            password="pass123",
            role="buyer",
        )
        self.buyer = BuyerProfile.objects.create(user=self.buyer_user)
        self.seller_user = User.objects.create_user(
            username="seller1",
            email="seller1@example.com",
            password="pass123",
            role="seller",
        )
        self.seller = SellerProfile.objects.create(user=self.seller_user)

    def create_task(self, title):
        return BuyerTasks.objects.create(
            buyer=self.buyer,
            title=title,
            platform="instagram",
            taskType="likes",
            url="https://example.com/post",
            goal=1,
            pricePerAction=1,
            status="active",
            approval_status="approved",
        )

    def test_seller_profile_database_default_rating_is_three_star(self):
        fresh_user = User.objects.create_user(
            username="freshseller",
            email="freshseller@example.com",
            password="pass123",
            role="seller",
        )
        fresh_seller = SellerProfile.objects.create(user=fresh_user)

        self.assertEqual(fresh_seller.ratings, 3)

    def test_history_with_no_completed_jobs_keeps_default_three_star_rating(self):
        task = self.create_task("Assigned but not completed")
        JobsHistory.objects.create(
            seller=self.seller,
            task=task,
            status="pending",
            proofStatus="pending",
            auditStatus="not_checked",
            completionTime=0,
        )

        rating_data = calculate_seller_rating(self.seller)

        self.assertEqual(rating_data["rating"], 3)
        self.assertEqual(rating_data["rating_source"], "new_seller_default")

    @patch("service.seller_rating.predict_rating_with_ml_model", return_value=None)
    def test_valid_completed_history_updates_rating_and_success_metrics(self, _mock_ml):
        for index in range(5):
            JobsHistory.objects.create(
                seller=self.seller,
                task=self.create_task(f"Valid job {index}"),
                status="completed",
                proofUrl=f"https://example.com/proof-{index}.png",
                proofStatus="valid",
                auditStatus="passed",
                completionTime=2,
                priceEarned=1,
            )

        rating_data = update_seller_rating(self.seller)
        self.seller.refresh_from_db()

        self.assertGreaterEqual(rating_data["rating"], 4)
        self.assertEqual(rating_data["success_rate"], 1.0)
        self.assertEqual(rating_data["proof_validity_rate"], 1.0)
        self.assertEqual(rating_data["audit_retention_rate"], 1.0)
        self.assertEqual(self.seller.ratings, rating_data["rating"])

    @patch("service.seller_rating.predict_rating_with_ml_model", return_value=None)
    def test_invalid_proofs_and_failed_audits_reduce_rating(self, _mock_ml):
        for index in range(3):
            JobsHistory.objects.create(
                seller=self.seller,
                task=self.create_task(f"Invalid job {index}"),
                status="completed",
                proofUrl=f"https://example.com/bad-proof-{index}.png",
                proofStatus="invalid",
                auditStatus="failed",
                completionTime=12,
                priceEarned=0,
            )

        rating_data = update_seller_rating(self.seller)
        self.seller.refresh_from_db()

        self.assertLessEqual(rating_data["rating"], 2)
        self.assertLess(rating_data["trust_score"], 50)
        self.assertEqual(self.seller.ratings, rating_data["rating"])

    def test_duplicate_seller_task_assignment_is_rejected(self):
        task = self.create_task("Unique task")
        JobsHistory.objects.create(seller=self.seller, task=task)

        with self.assertRaises(Exception):
            JobsHistory.objects.create(seller=self.seller, task=task)

    def test_valid_proof_review_creates_seller_behavior_log(self):
        job = JobsHistory.objects.create(
            seller=self.seller,
            task=self.create_task("Behavior log task"),
            status="completed",
            proofUrl="https://example.com/proof.png",
            proofStatus="pending",
        )

        response = self.client.post(
            f"/api/seller-proof/{job.id}/review/",
            data='{"proofStatus": "valid"}',
            content_type="application/json",
            HTTP_X_DEVICE_ID="test-device-123",
            HTTP_USER_AGENT="EngageX Test Browser",
            REMOTE_ADDR="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SellerBehaviorLog.objects.count(), 1)
        behavior_log = SellerBehaviorLog.objects.get()
        self.assertEqual(behavior_log.job, job)
        self.assertEqual(behavior_log.task_id, str(job.task.id))
        self.assertEqual(behavior_log.seller_id, str(self.seller.id))
        self.assertEqual(behavior_log.ip_address, "127.0.0.1")
        self.assertEqual(behavior_log.device_id, "test-device-123")
        self.assertEqual(behavior_log.user_agent, "EngageX Test Browser")
