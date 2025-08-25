# Refactorización: Escribiendo Código Más Limpio y Reutilizable

El código anterior funciona, pero repetimos el mismo cálculo dos veces. En programación, seguimos un principio llamado **DRY (Don't Repeat Yourself - No te repitas)**.

**Refactorizar** significa mejorar la estructura del código sin cambiar su funcionalidad. Crearemos una **función** para encapsular la lógica de conversión. Esto nos da varias ventajas:

1.  **Reutilización:** Podemos llamar a la función cuantas veces queramos sin reescribir la fórmula.
2.  **Legibilidad:** El código principal se vuelve más corto y fácil de entender.
3.  **Mantenimiento:** Si necesitamos corregir un error en la fórmula, solo lo hacemos en un lugar: dentro de la función.
