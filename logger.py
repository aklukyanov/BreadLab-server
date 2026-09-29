import logging


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",  # 👈 Вот оно
    datefmt="%H:%M:%S"
)

crud_recipes_logger = logging.getLogger("CRUD_RECIPES_LOGGER")
crud_users_logger = logging.getLogger("CRUD_USERS_LOGGER")
crud_baking_sessions_logger = logging.getLogger("CRUD_BAKING_SESSIONS_LOGGER")
crud_baking_notes_logger = logging.getLogger("CRUD_BAKING_NOTES_LOGGER")
llm_client_logger = logging.getLogger("LLM_CLIENT_LOGGER")
options_logger = logging.getLogger("OPTIONS_LOGGER")
