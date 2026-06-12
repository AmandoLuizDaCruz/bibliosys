function somenteNumeros(valor) {
    return valor.replace(/\D/g, "");
}


function formatarCPF(valor) {
    const numeros = somenteNumeros(valor).slice(0, 11);

    if (numeros.length <= 3) {
        return numeros;
    }

    if (numeros.length <= 6) {
        return `${numeros.slice(0, 3)}.${numeros.slice(3)}`;
    }

    if (numeros.length <= 9) {
        return (
            `${numeros.slice(0, 3)}.` +
            `${numeros.slice(3, 6)}.` +
            `${numeros.slice(6)}`
        );
    }

    return (
        `${numeros.slice(0, 3)}.` +
        `${numeros.slice(3, 6)}.` +
        `${numeros.slice(6, 9)}-` +
        `${numeros.slice(9)}`
    );
}


function formatarTelefone(valor) {
    const numeros = somenteNumeros(valor).slice(0, 11);

    if (numeros.length === 0) {
        return "";
    }

    if (numeros.length <= 2) {
        return `(${numeros}`;
    }

    if (numeros.length <= 6) {
        return (
            `(${numeros.slice(0, 2)}) ` +
            `${numeros.slice(2)}`
        );
    }

    if (numeros.length <= 10) {
        return (
            `(${numeros.slice(0, 2)}) ` +
            `${numeros.slice(2, 6)}-` +
            `${numeros.slice(6)}`
        );
    }

    return (
        `(${numeros.slice(0, 2)}) ` +
        `${numeros.slice(2, 7)}-` +
        `${numeros.slice(7)}`
    );
}


document.addEventListener("DOMContentLoaded", function () {
    const camposCPF = document.querySelectorAll(
        '[data-mask="cpf"]'
    );

    camposCPF.forEach(function (campo) {
        campo.value = formatarCPF(campo.value);

        campo.addEventListener("input", function () {
            campo.value = formatarCPF(campo.value);
        });
    });

    const camposTelefone = document.querySelectorAll(
        '[data-mask="telefone"]'
    );

    camposTelefone.forEach(function (campo) {
        campo.value = formatarTelefone(campo.value);

        campo.addEventListener("input", function () {
            campo.value = formatarTelefone(campo.value);
        });
    });
});
