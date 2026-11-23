import redis


class EpiasTokenManager:
    def __init__(self, redis_url: str, user_id: int):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)

        self.key = f"epias:user:{user_id}:tgt"
        self.lock_key = f"epias:user:{user_id}:tgt:lock"

    def get_token(self, create_token):
        token=self.redis.get(self.key)

        if token:
            return token

        with self.redis.lock(
            self.lock_key,
            timeout=30,
            blocking_timeout=10
        ):
            token = self.redis.get(self.key)

            if token:
                return token

            token = create_token()

            if not token:
                raise RuntimeError("EPİAS TGT Token Alınmadı!")

            self.redis.setex(
                self.key,
                300,
                token
            )

            return token