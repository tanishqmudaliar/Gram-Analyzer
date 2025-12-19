from datetime import datetime
from typing import Optional
from .models import (
    InstagramUser,
    AnalyticsOverview,
    DetailedAnalytics,
)
from .database import database, followers_snapshot, following_snapshot, analytics_cache


class AnalyticsService:
    """Service for computing Instagram analytics."""

    def compute_analytics(
        self,
        followers: list[InstagramUser],
        following: list[InstagramUser],
        previous_followers: Optional[list[InstagramUser]] = None,
    ) -> DetailedAnalytics:
        """
        Compute all analytics from follower/following data.
        """
        # Create sets for efficient lookup
        follower_ids = {f.ig_id for f in followers}
        following_ids = {f.ig_id for f in following}
        follower_map = {f.ig_id: f for f in followers}
        following_map = {f.ig_id: f for f in following}

        # People you follow who don't follow you back
        not_following_back_ids = following_ids - follower_ids
        not_following_back = [following_map[id] for id in not_following_back_ids]

        # People who follow you but you don't follow back
        not_followed_back_ids = follower_ids - following_ids
        not_followed_back = [follower_map[id] for id in not_followed_back_ids]

        # Mutual friends (follow each other)
        mutual_ids = follower_ids & following_ids
        mutual_friends = [follower_map[id] for id in mutual_ids]

        # New and lost followers
        new_followers = []
        lost_followers = []

        if previous_followers:
            previous_follower_ids = {f.ig_id for f in previous_followers}
            previous_follower_map = {f.ig_id: f for f in previous_followers}

            # New followers (in current but not in previous)
            new_follower_ids = follower_ids - previous_follower_ids
            new_followers = [follower_map[id] for id in new_follower_ids]

            # Lost followers (in previous but not in current)
            lost_follower_ids = previous_follower_ids - follower_ids
            lost_followers = [previous_follower_map[id] for id in lost_follower_ids]

        # TODO: Story viewer feature - not yet implemented
        # Ghost followers would be computed from story_viewer_history when implemented
        ghost_followers = []

        # Build overview
        overview = AnalyticsOverview(
            total_followers=len(followers),
            total_following=len(following),
            not_following_back=len(not_following_back),
            not_followed_back=len(not_followed_back),
            mutual_friends=len(mutual_friends),
            new_followers=len(new_followers),
            lost_followers=len(lost_followers),
            last_sync=datetime.utcnow(),
        )

        return DetailedAnalytics(
            overview=overview,
            followers=sorted(followers, key=lambda x: x.username.lower()),
            following=sorted(following, key=lambda x: x.username.lower()),
            not_following_back=sorted(not_following_back, key=lambda x: x.username.lower()),
            not_followed_back=sorted(not_followed_back, key=lambda x: x.username.lower()),
            mutual_friends=sorted(mutual_friends, key=lambda x: x.username.lower()),
            new_followers=new_followers,
            lost_followers=lost_followers,
            ghost_followers=ghost_followers[:100],  # Limit to 100
        )

    async def save_snapshot(
        self,
        user_id: int,
        followers: list[InstagramUser],
        following: list[InstagramUser],
    ) -> None:
        """Save current followers/following to database for historical comparison."""
        snapshot_date = datetime.utcnow()

        # Save followers
        for follower in followers:
            await database.execute(
                followers_snapshot.insert().values(
                    user_id=user_id,
                    snapshot_date=snapshot_date,
                    follower_ig_id=follower.ig_id,
                    follower_username=follower.username,
                    follower_full_name=follower.full_name,
                    follower_profile_pic_url=follower.profile_pic_url,
                    is_verified=follower.is_verified,
                    is_private=follower.is_private,
                )
            )

        # Save following
        for follow in following:
            await database.execute(
                following_snapshot.insert().values(
                    user_id=user_id,
                    snapshot_date=snapshot_date,
                    following_ig_id=follow.ig_id,
                    following_username=follow.username,
                    following_full_name=follow.full_name,
                    following_profile_pic_url=follow.profile_pic_url,
                    is_verified=follow.is_verified,
                    is_private=follow.is_private,
                )
            )

    async def get_previous_followers(self, user_id: int) -> Optional[list[InstagramUser]]:
        """Get the most recent previous follower snapshot."""
        # Get the latest snapshot date that's not today
        query = """
            SELECT DISTINCT snapshot_date
            FROM followers_snapshot
            WHERE user_id = :user_id
            ORDER BY snapshot_date DESC
            LIMIT 2
        """
        rows = await database.fetch_all(query, {"user_id": user_id})

        if len(rows) < 2:
            return None

        # Get the second most recent snapshot
        previous_date = rows[1]["snapshot_date"]

        query = followers_snapshot.select().where(
            (followers_snapshot.c.user_id == user_id)
            & (followers_snapshot.c.snapshot_date == previous_date)
        )
        rows = await database.fetch_all(query)

        return [
            InstagramUser(
                ig_id=row["follower_ig_id"],
                username=row["follower_username"],
                full_name=row["follower_full_name"],
                profile_pic_url=row["follower_profile_pic_url"],
                is_verified=row["is_verified"],
                is_private=row["is_private"],
            )
            for row in rows
        ]

    async def cache_analytics(self, user_id: int, analytics: DetailedAnalytics) -> None:
        """Cache computed analytics."""
        data = analytics.model_dump_json()

        # Upsert
        existing = await database.fetch_one(
            analytics_cache.select().where(analytics_cache.c.user_id == user_id)
        )

        if existing:
            await database.execute(
                analytics_cache.update()
                .where(analytics_cache.c.user_id == user_id)
                .values(data=data, computed_at=datetime.utcnow())
            )
        else:
            await database.execute(
                analytics_cache.insert().values(
                    user_id=user_id, data=data, computed_at=datetime.utcnow()
                )
            )

    async def get_cached_analytics(self, user_id: int) -> Optional[DetailedAnalytics]:
        """Get cached analytics if available."""
        row = await database.fetch_one(
            analytics_cache.select().where(analytics_cache.c.user_id == user_id)
        )

        if row:
            return DetailedAnalytics.model_validate_json(row["data"])
        return None


# Singleton instance
analytics_service = AnalyticsService()
