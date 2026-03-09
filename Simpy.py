import random
import simpy
import statistics
import matplotlib.pyplot as plt


RANDOM_SEED       = 123
PROCESOS          = [25, 50, 100, 150, 200]
INTERVALOS        = [10.0, 5.0, 1.0]
MIN_MEMORIA       = 1
MAX_MEMORIA       = 10
MIN_INSTRUCCIONES = 1
MAX_INSTRUCCIONES = 10

colores   = {10.0: "#4C9BE8", 5.0: "#E8834C", 1.0: "#4CE8A0"}
etiquetas = {10.0: "Intervalo 10", 5.0: "Intervalo 5", 1.0: "Intervalo 1"}

RAM = None
CPU = None
TIEMPOS_TOTALES = []


class proceso(object):
    def __init__(self, id, env, inst_por_tick):
        self.env = env
        self.name = id
        self.memoria = random.randint(MIN_MEMORIA, MAX_MEMORIA)
        self.instrucciones = random.randint(MIN_INSTRUCCIONES, MAX_INSTRUCCIONES)  
        self.tiempo_llegada = env.now
        self.inst_por_tick = inst_por_tick
        self.action = env.process(self.new())

    def new(self):
        yield RAM.get(self.memoria)
        self.env.process(self.ready())

    def ready(self):
        with CPU.request() as req:
            yield req
            yield self.env.process(self.running())

    def running(self):
        yield self.env.timeout(1)
        self.instrucciones = max(0, self.instrucciones - self.inst_por_tick)
        asignacion = random.randint(1, 2)
        if self.instrucciones == 0:
            self.env.process(self.terminated())
        elif asignacion == 1:
            self.env.process(self.waiting())
        else:
            self.env.process(self.ready())

    def waiting(self):
        tiempo_espera = random.randint(1, 10)
        yield self.env.timeout(tiempo_espera)
        self.env.process(self.ready())

    def terminated(self):
        termino = self.env.now
        tiempo_total = termino - self.tiempo_llegada
        yield RAM.put(self.memoria)
        TIEMPOS_TOTALES.append(tiempo_total)

def source(env, num_procesos, interval, inst_por_tick):
    for i in range(num_procesos):
        p = proceso("Proceso %d" % i, env, inst_por_tick)
        t = random.expovariate(1.0 / interval)
        yield env.timeout(t)

# ── Función de simulación ─────────────────────────────────────────────────────
def correr_escenario(ram_cap, num_cpus, inst_por_tick):
    global RAM, CPU, TIEMPOS_TOTALES
    res = {iv: {"promedios": [], "desviaciones": []} for iv in INTERVALOS}

    for num_procesos in PROCESOS:
        for interval in INTERVALOS:
            random.seed(RANDOM_SEED)
            TIEMPOS_TOTALES = []
            env = simpy.Environment()
            RAM = simpy.Container(env, init=ram_cap, capacity=ram_cap)
            CPU = simpy.Resource(env, capacity=num_cpus)
            env.process(source(env, num_procesos, interval, inst_por_tick))
            env.run()

            if TIEMPOS_TOTALES:
                prom = statistics.mean(TIEMPOS_TOTALES)
                desv = statistics.stdev(TIEMPOS_TOTALES) if len(TIEMPOS_TOTALES) > 1 else 0
            else:
                prom, desv = 0, 0

            res[interval]["promedios"].append(prom)
            res[interval]["desviaciones"].append(desv)

    return res


def graficar(res, titulo_prom, titulo_desv, archivo_prom, archivo_desv):
    plt.figure(figsize=(8, 5))
    for iv in INTERVALOS:
        plt.plot(PROCESOS, res[iv]["promedios"],
                 marker="o", color=colores[iv], label=etiquetas[iv],
                 linewidth=2, markersize=7)
    plt.title(titulo_prom)
    plt.xlabel("Número de Procesos")
    plt.ylabel("Tiempo Promedio")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(archivo_prom, dpi=150)
    plt.show()
    print(f"  Guardada: {archivo_prom}")

    plt.figure(figsize=(8, 5))
    for iv in INTERVALOS:
        plt.plot(PROCESOS, res[iv]["desviaciones"],
                 marker="s", color=colores[iv], label=etiquetas[iv],
                 linewidth=2, markersize=7)
    plt.title(titulo_desv)
    plt.xlabel("Número de Procesos")
    plt.ylabel("Desviación Estándar")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(archivo_desv, dpi=150)
    plt.show()
    print(f"  Guardada: {archivo_desv}")


print("\n" + "="*55)
print("Base (RAM=100, 1 CPU, 3 inst/tick)")
print("="*55)
res_base = correr_escenario(ram_cap=100, num_cpus=1, inst_por_tick=3)

for i, num_procesos in enumerate(PROCESOS):
    for iv in INTERVALOS:
        print(f"  Procesos={num_procesos:3d}  Intervalo={iv:4.1f} "
              f"| Prom={res_base[iv]['promedios'][i]:7.4f}  "
              f"Desv={res_base[iv]['desviaciones'][i]:7.4f}")

graficar(res_base,
         "Promedio de tiempo (base)",
         "Desviación estándar (base)",
         "base_promedios.png",          
         "base_desviaciones.png")


print("\n" + "="*55)
print("3a — RAM=200, 1 CPU, 3 inst/tick")
print("="*55)
res_3a = correr_escenario(ram_cap=200, num_cpus=1, inst_por_tick=3)

graficar(res_3a,
         "Promedio (RAM=200)",
         "Desviación estándar (RAM=200)",
         "ram200_promedios.png",
         "ram200_desviaciones.png")

print("\n" + "="*55)
print("3b — RAM=100, 1 CPU rápido (6 inst/tick)")
print("="*55)
res_3b = correr_escenario(ram_cap=100, num_cpus=1, inst_por_tick=6)

graficar(res_3b,
         "Promedio (CPU 6 inst/tick)",
         "Desviación estándar (CPU 6 inst/tick)",
         "cpu_rapido_promedios.png",
         "cpu_rapido_desviaciones.png")

print("\n" + "="*55)
print("3c — RAM=100, 2 CPUs, 3 inst/tick")
print("="*55)
res_3c = correr_escenario(ram_cap=100, num_cpus=2, inst_por_tick=3)

graficar(res_3c,
         "Promedio (2 CPUs)",
         "Desviación estándar (2 CPUs)",
         "2cpus_promedios.png",
         "2cpus_desviaciones.png")


print("\n" + "="*55)
print("Comparación de estrategias (intervalo=1)")
print("="*55)

iv = 1.0
estrategias = {
    "Base (RAM=100, 1CPU, 3inst)": res_base[iv]["promedios"],
    "3a: RAM=200":                 res_3a[iv]["promedios"],
    "3b: CPU rápido (6inst)":      res_3b[iv]["promedios"],
    "3c: 2 CPUs":                  res_3c[iv]["promedios"],
}
colores_comp = ["#888888", "#4C9BE8", "#E8834C", "#4CE8A0"]

plt.figure(figsize=(9, 6))
for (label, promedios), color in zip(estrategias.items(), colores_comp):
    plt.plot(PROCESOS, promedios, marker="o", label=label,
             color=color, linewidth=2, markersize=7)
plt.title("Comparación de estrategias (intervalo=1)")
plt.xlabel("Número de Procesos")
plt.ylabel("Tiempo Promedio")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("comparacion.png", dpi=150)
plt.show()