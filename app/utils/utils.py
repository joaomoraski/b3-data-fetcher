def format_cnpj(cnpj: str) -> str | None:
    return "{}.{}.{}/{}-{}".format(
        cnpj[:2], cnpj[2:5], cnpj[5:8], cnpj[8:12], cnpj[12:14]
    )
