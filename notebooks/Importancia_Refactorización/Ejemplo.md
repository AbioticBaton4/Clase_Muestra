# Calculadora de Rango de IPs

## Problema Propuesto

Objetivo: Crear un programa en Python que solicite al usuario dos direcciones IPv4, una de inicio y una de fin, y calcule cuántas direcciones IP utilizables hay entre ellas.

Ejemplos de IPv4 a usar:
* IP: 192.168.0.50
* IP: 192.168.1.10

Salida esperada: 216

## ¿Para qué sirve esto en el mundo real? 🤔

Calcular el rango entre direcciones IP es una tarea fundamental para los administradores de redes. Les permite saber cuántos dispositivos (computadoras, teléfonos, etc.) pueden conectarse en un segmento de red específico. Esto es crucial para:

* **Planificación de redes:** Asegurarse de que haya suficientes direcciones para todos los dispositivos.
* **Seguridad:** Definir reglas de firewall que apliquen a un rango específico de IPs.
* **Diagnóstico:** Identificar si un dispositivo está dentro del rango esperado.

## ¿Qué es una Dirección IPv4? Un Repaso Rápido

Una dirección **IPv4** es como el domicilio de un dispositivo en una red. Se compone de **cuatro números** separados por puntos, a los que llamamos **octetos**.

`192.168.1.10` -> `[192]` `[168]` `[1]` `[10]`

Cada octeto es, en realidad, un número de 8 bits, lo que significa que su valor solo puede ir de **0** a **255** (porque $2^8 = 256$ valores posibles). Para que las computadoras puedan hacer cálculos con ellas, necesitamos una forma de convertirlas a un número entero único. ¡Y eso es exactamente lo que haremos!

## Solución 

### La Magia de la Base 256

¿Cómo convertimos `A.B.C.D` a un solo número? Usando la misma lógica que usamos con los números decimales (base 10), pero en **base 256**.

Pensemos en el número `123`. Realmente significa:
$$ (1 \times 10^2) + (2 \times 10^1) + (3 \times 10^0) $$

Una dirección IP funciona igual, pero en lugar de potencias de 10, usamos **potencias de 256**, porque cada octeto puede tener 256 valores posibles.

$$ \text{Valor Entero} = (A \times 256^3) + (B \times 256^2) + (C \times 256^1) + (D \times 256^0) $$

Como $256^1 = 256$ y $256^0 = 1$, la fórmula simplificada es:

$$ \text{Valor Entero} = (A \times 16,777,216) + (B \times 65,536) + (C \times 256) + D $$