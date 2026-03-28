from __future__ import annotations


class ApartmentNotFound(Exception):
    pass


class ApartmentAlreadyDeleted(Exception):
    pass


class UnauthorizedApartmentAccess(Exception):
    pass