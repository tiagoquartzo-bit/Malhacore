import uvicorn
from config.settings import settings

if __name__ == "__main__":
    print("=" * 70)
    print(" MALHACORE - NÚCLEO DE COMANDO & AUDITORIA FINANCEIRA")
    print(" STATUS: OPERACIONAL | BANCO: SQLITE LOCAL | CUSTO: R$ 0,00")
    print(f" ACESSO LOCAL: http://{settings.HOST}:{settings.PORT}")
    print("=" * 70)
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
