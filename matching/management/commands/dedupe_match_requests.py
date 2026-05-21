from collections import defaultdict

from django.core.management.base import BaseCommand

from matching.models import MatchRequest


STATUS_PRIORITY = {
    "completed": 4,
    MatchRequest.ACCEPTED: 3,
    MatchRequest.PENDING: 2,
    MatchRequest.DECLINED: 1,
    MatchRequest.CANCELLED: 1,
}


class Command(BaseCommand):
    help = "Find or remove duplicate match requests, keeping the newest highest-status request per exchange pair."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Delete duplicate rows. Without this flag the command only reports what would change.",
        )

    def handle(self, *args, **options):
        grouped_requests = defaultdict(list)
        requests = MatchRequest.objects.select_related(
            "sender",
            "receiver",
            "offered_skill",
            "requested_skill",
        ).order_by("sender_id", "receiver_id", "offered_skill_id", "requested_skill_id", "-updated_at", "-pk")

        for match_request in requests:
            grouped_requests[
                (
                    match_request.sender_id,
                    match_request.receiver_id,
                    match_request.offered_skill_id,
                    match_request.requested_skill_id,
                )
            ].append(match_request)

        duplicate_groups = [group for group in grouped_requests.values() if len(group) > 1]
        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS("No duplicate match requests found."))
            return

        delete_ids = []
        for group in duplicate_groups:
            keeper = max(group, key=self._request_rank)
            duplicates = [request for request in group if request.pk != keeper.pk]
            delete_ids.extend(request.pk for request in duplicates)
            self.stdout.write(
                f"Keeping request #{keeper.pk} ({keeper.status}) for "
                f"{keeper.sender} -> {keeper.receiver}; duplicates: "
                f"{', '.join(str(request.pk) for request in duplicates)}"
            )

        if options["apply"]:
            deleted, _ = MatchRequest.objects.filter(pk__in=delete_ids).delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} duplicate match request row(s)."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run only. Re-run with --apply to delete {len(delete_ids)} duplicate row(s)."
                )
            )

    def _request_rank(self, match_request):
        has_exchange = hasattr(match_request, "exchange")
        return (
            STATUS_PRIORITY.get(match_request.status, 0),
            int(has_exchange),
            match_request.updated_at,
            match_request.created_at,
            match_request.pk,
        )
