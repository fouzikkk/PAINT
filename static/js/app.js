document.addEventListener('DOMContentLoaded', function () {
    ustawRok();
    menuMobilne();
    wybórLogowania();
    walidacjaFormularzy();
    pokazHaslo();
    potwierdzeniaAkcji();
    modale();
});

function ustawRok() {
    var pola = document.querySelectorAll('[data-current-year]');
    var rok = new Date().getFullYear();

    for (var i = 0; i < pola.length; i++) {
        pola[i].textContent = rok;
    }
}

function menuMobilne() {
    var przycisk = document.querySelector('[data-nav-toggle]');
    var menu = document.querySelector('[data-main-nav]');
    var akcje = document.querySelector('[data-nav-actions]');

    if (przycisk == null || menu == null) {
        return;
    }

    przycisk.onclick = function () {
        var otwarte = menu.classList.toggle('is-open');
        if (akcje != null) {
            akcje.classList.toggle('is-open', otwarte);
        }
        przycisk.setAttribute('aria-expanded', otwarte ? 'true' : 'false');
    };
}

function wybórLogowania() {
    var wybóry = document.querySelectorAll('[data-auth-choice]');
    var panele = document.querySelectorAll('[data-auth-panel]');
    var etykiety = document.querySelectorAll('[data-auth-label]');

    if (wybóry.length === 0 || panele.length === 0) {
        return;
    }

    function pokazPanel(wartosc) {
        for (var i = 0; i < panele.length; i++) {
            if (panele[i].getAttribute('data-auth-panel') === wartosc) {
                panele[i].classList.remove('hidden');
            } else {
                panele[i].classList.add('hidden');
            }
        }

        for (var j = 0; j < etykiety.length; j++) {
            if (etykiety[j].getAttribute('data-auth-label') === wartosc) {
                etykiety[j].classList.add('active');
            } else {
                etykiety[j].classList.remove('active');
            }
        }
    }

    for (var k = 0; k < wybóry.length; k++) {
        wybóry[k].onchange = function () {
            pokazPanel(this.value);
        };
    }

    var aktywny = document.querySelector('[data-auth-choice]:checked');
    if (aktywny != null) {
        pokazPanel(aktywny.value);
    }
}

function walidacjaFormularzy() {
    var formularze = document.querySelectorAll('form[data-validate]');

    for (var i = 0; i < formularze.length; i++) {
        formularze[i].onsubmit = function (event) {
            usunKomunikat(this);

            var blad = sprawdzFormularz(this);
            if (blad !== '') {
                event.preventDefault();
                pokazKomunikat(this, blad, 'error');
                return false;
            }
        };
    }
}

function sprawdzFormularz(formularz) {
    var wymagane = formularz.querySelectorAll('[required]');

    for (var i = 0; i < wymagane.length; i++) {
        var pole = wymagane[i];

        if (pole.type === 'checkbox') {
            if (pole.checked === false) {
                return 'Zaznacz wymagane oświadczenie.';
            }
        } else if (pole.value.trim() === '') {
            return 'Uzupełnij pole: ' + etykietaPola(pole) + '.';
        }
    }

    var emaile = formularz.querySelectorAll('input[type="email"]');
    for (var j = 0; j < emaile.length; j++) {
        if (emaile[j].value.trim() !== '' && poprawnyEmail(emaile[j].value) === false) {
            return 'Podaj poprawny adres e-mail.';
        }
    }

    var haslo = formularz.querySelector('[name="password"]');
    var haslo2 = formularz.querySelector('[name="password_repeat"]');
    if (haslo != null && haslo2 != null && haslo.value !== haslo2.value) {
        return 'Hasła muszą być takie same.';
    }

    if (haslo != null && haslo.value !== '' && /\d/.test(haslo.value) === false) {
        return 'Hasło musi zawierać co najmniej jedną cyfrę.';
    }

    var noweHaslo = formularz.querySelector('[name="new_password1"]');
    if (noweHaslo != null && noweHaslo.value !== '' && /\d/.test(noweHaslo.value) === false) {
        return 'Hasło musi zawierać co najmniej jedną cyfrę.';
    }

    var nowyEmail = formularz.querySelector('[name="new_email"]');
    var nowyEmail2 = formularz.querySelector('[name="new_email_repeat"]');
    if (nowyEmail != null && nowyEmail2 != null && nowyEmail.value !== nowyEmail2.value) {
        return 'Adresy e-mail muszą być takie same.';
    }

    var telefony = formularz.querySelectorAll('[name="phone"], [name="phone_number"]');
    for (var k = 0; k < telefony.length; k++) {
        if (telefony[k].value.trim() !== '' && poprawnyTelefon(telefony[k].value) === false) {
            return 'Numer telefonu musi składać się dokładnie z 9 cyfr.';
        }
    }

    return '';
}

function poprawnyEmail(email) {
    var wzor = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return wzor.test(email.trim());
}

function poprawnyTelefon(telefon) {
    var wzor = /^[0-9]{9}$/;
    return wzor.test(telefon.trim());
}

function etykietaPola(pole) {
    var rodzic = pole.parentNode;
    if (rodzic != null) {
        var label = rodzic.querySelector('label');
        if (label != null) {
            return label.textContent.replace('*', '').trim();
        }
    }
    return pole.name;
}

function pokazKomunikat(formularz, tekstKomunikatu, typ) {
    var komunikat = document.createElement('div');
    komunikat.className = 'form-message ' + typ;
    komunikat.textContent = tekstKomunikatu;
    formularz.insertBefore(komunikat, formularz.firstChild);
}

function usunKomunikat(formularz) {
    var komunikat = formularz.querySelector('.form-message');
    if (komunikat != null) {
        formularz.removeChild(komunikat);
    }
}

function pokazHaslo() {
    var przyciski = document.querySelectorAll('[data-password-button]');

    for (var i = 0; i < przyciski.length; i++) {
        przyciski[i].onclick = function () {
            var idPola = this.getAttribute('data-password-button');
            var pole = document.querySelector(idPola);

            if (pole == null) {
                return;
            }

            if (pole.type === 'password') {
                pole.type = 'text';
                this.textContent = 'Ukryj';
            } else {
                pole.type = 'password';
                this.textContent = 'Pokaż';
            }
        };
    }
}

function potwierdzeniaAkcji() {
    var przyciski = document.querySelectorAll('[data-confirm]');

    for (var i = 0; i < przyciski.length; i++) {
        przyciski[i].onclick = function (event) {
            var komunikat = this.getAttribute('data-confirm');
            if (komunikat && window.confirm(komunikat) === false) {
                event.preventDefault();
                return false;
            }
        };
    }
}

function modale() {
    var otwieracze = document.querySelectorAll('[data-modal-open]');
    var zamykacze = document.querySelectorAll('[data-modal-close]');
    var okna = document.querySelectorAll('dialog[data-modal]');

    for (var i = 0; i < otwieracze.length; i++) {
        otwieracze[i].onclick = function () {
            var idOkna = this.getAttribute('data-modal-open');
            var okno = document.getElementById(idOkna);

            if (okno == null) {
                return;
            }

            if (typeof okno.showModal === 'function') {
                okno.showModal();
            } else {
                okno.setAttribute('open', 'open');
            }
        };
    }

    for (var j = 0; j < zamykacze.length; j++) {
        zamykacze[j].onclick = function () {
            var okno = this.closest('dialog');

            if (okno == null) {
                return;
            }

            if (typeof okno.close === 'function') {
                okno.close();
            } else {
                okno.removeAttribute('open');
            }
        };
    }

    for (var k = 0; k < okna.length; k++) {
        okna[k].addEventListener('click', function (event) {
            if (event.target === this && typeof this.close === 'function') {
                this.close();
            }
        });
    }
}
