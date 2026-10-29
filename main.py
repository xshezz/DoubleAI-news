import random


def tas_kagit_makas():
    secenekler = ["taş", "kağıt", "makas"]

    oyuncu_skor = 0
    bilgisayar_skor = 0

    print("=" * 40)
    print(" TAŞ - KAĞIT - MAKAS OYUNUNA HOŞ GELDİNİZ! ")
    print("=" * 40)
    print("Oyundan çıkmak için 'çıkış' yazabilirsiniz.\n")

    while True:
        # Oyuncudan hamle alma
        oyuncu_secimi = (
            input("Seçiminiz (taş, kağıt, makas): ").strip().lower()
        )

        # Çıkış kontrolü
        if oyuncu_secimi == "çıkış":
            print("\nOyun bitti!")
            print(
                f"Son Skor -> Siz: {oyuncu_skor} | Bilgisayar: {bilgisayar_skor}"
            )
            print("Oynadığınız için teşekkürler!")
            break

        # Geçersiz girdi kontrolü
        if oyuncu_secimi not in secenekler:
            print(
                "❌ Geçersiz bir seçim yaptınız! Lütfen 'taş', 'kağıt' veya 'makas' yazın.\n"
            )
            continue

        # Bilgisayarın seçimi
        bilgisayar_secimi = random.choice(secenekler)
        print(f"Bilgisayarın Seçimi: {bilgisayar_secimi}")

        # Kazananı belirleme mantığı
        if oyuncu_secimi == bilgisayar_secimi:
            print("🤝 Berabere!")
        elif (
            (oyuncu_secimi == "taş" and bilgisayar_secimi == "makas")
            or (oyuncu_secimi == "kağıt" and bilgisayar_secimi == "taş")
            or (oyuncu_secimi == "makas" and bilgisayar_secimi == "kağıt")
        ):
            print("🎉 Bu turu siz kazandınız!")
            oyuncu_skor += 1
        else:
            print("🤖 Bu turu bilgisayar kazandı!")
            bilgisayar_skor += 1

        # Anlık skoru gösterme
        print(
            f"Mevcut Skor -> Siz: {oyuncu_skor} | Bilgisayar: {bilgisayar_skor}"
        )
        print("-" * 40)


# Oyunu başlat
if __name__ == "__main__":
    tas_kagit_makas()
