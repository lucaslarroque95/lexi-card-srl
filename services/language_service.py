import uuid
from datetime import datetime
from typing import List, Optional

from models.language import Language
from models.user_language import UserLanguage
from repositories.language_repository import LanguageRepository
from repositories.user_language_repository import UserLanguageRepository
from services.common_languages import COMMON_LANGUAGES


class LanguageService:
    def __init__(self, language_repository: LanguageRepository, user_language_repository: UserLanguageRepository):
        self.language_repository = language_repository
        self.user_language_repository = user_language_repository

    def create_language(self, language: Language, user_id: uuid.UUID, started_at: Optional[datetime] = None) -> Language:
        created = self.language_repository.create(language)
        self.user_language_repository.create(
            UserLanguage(user_id=user_id, language_id=created.id, started_at=started_at or datetime.now())
        )
        return created

    def get_language(self, language_id: uuid.UUID) -> Optional[Language]:
        return self.language_repository.get(language_id)

    def list_languages(self, user_id: uuid.UUID) -> List[Language]:
        """Los idiomas del usuario, completando primero los de COMMON_LANGUAGES
        que todavía no tenga. Los idiomas son por usuario (concepts/rules
        chequean que el language_id sea suyo), así que la lista común se
        siembra por usuario en vez de ser una tabla global aparte."""
        existing = self.language_repository.get_by_user(user_id)
        known_codes = {language.code for language in existing}
        for code, name in COMMON_LANGUAGES:
            if code not in known_codes:
                existing.append(self.language_repository.create(Language(user_id=user_id, name=name, code=code)))

        # Dos listados en paralelo del mismo usuario nuevo pueden sembrar el
        # mismo código dos veces: se devuelve uno por código, los comunes
        # primero y en su orden, después los que haya creado el usuario.
        by_code = {}
        for language in existing:
            by_code.setdefault(language.code, language)
        order = {code: i for i, (code, _) in enumerate(COMMON_LANGUAGES)}
        return sorted(by_code.values(), key=lambda lang: (order.get(lang.code, len(order)), lang.name))

    def update_language(self, language_id: uuid.UUID, language: Language) -> Optional[Language]:
        return self.language_repository.update(language_id, language)

    def delete_language(self, language_id: uuid.UUID) -> bool:
        return self.language_repository.delete(language_id)
