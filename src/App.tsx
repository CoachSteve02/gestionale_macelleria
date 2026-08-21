/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { motion } from 'motion/react';
import { Database, FileCode, FileSpreadsheet, Download, LayoutDashboard } from 'lucide-react';

export default function App() {
  return (
    <div className="min-h-screen bg-neutral-100 flex flex-col font-sans">
      <div className="flex-1 max-w-4xl w-full mx-auto p-6 flex flex-col justify-center">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-xl overflow-hidden"
        >
          <div className="bg-emerald-600 p-8 text-white">
            <h1 className="text-3xl font-bold mb-2">Gestionale Macelleria (HACCP)</h1>
            <p className="text-emerald-100 text-lg">
              Architettura Python/Flask completata con successo!
            </p>
          </div>
          
          <div className="p-8">
            <div className="mb-8 text-neutral-700 text-lg">
              <p className="mb-4">
                Hai richiesto un'architettura software basata su <strong>Python, Flask, PostgreSQL e Jinja2</strong>. 
                Poiché questo ambiente (AI Studio) è ottimizzato per l'esecuzione nativa di applicazioni React/Node.js, 
                ho generato esattamente i file richiesti e li ho salvati nella root del tuo progetto.
              </p>
              <p>
                Tutto il codice è pronto per essere scaricato e avviato localmente, rispettando al 100% 
                la "Regola dei 3 Click", l'export in Excel e le logiche Poka-Yoke.
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <div className="bg-neutral-50 p-6 rounded-xl border border-neutral-200">
                <Database className="w-8 h-8 text-blue-500 mb-4" />
                <h3 className="font-bold text-neutral-900 mb-2">Schema SQL (PostgreSQL)</h3>
                <p className="text-sm text-neutral-600">File: <code>database.sql</code><br/>Include DDL completo, vista etichette e insert DML iniziali divisi in Tagli, Vari e Preparati.</p>
              </div>
              
              <div className="bg-neutral-50 p-6 rounded-xl border border-neutral-200">
                <FileCode className="w-8 h-8 text-emerald-500 mb-4" />
                <h3 className="font-bold text-neutral-900 mb-2">Backend Flask</h3>
                <p className="text-sm text-neutral-600">File: <code>app.py</code><br/>Gestione del Connection Pool (psycopg2), rotte Poka-Yoke e logica di tracciabilità ricette automatica.</p>
              </div>

              <div className="bg-neutral-50 p-6 rounded-xl border border-neutral-200">
                <LayoutDashboard className="w-8 h-8 text-orange-500 mb-4" />
                <h3 className="font-bold text-neutral-900 mb-2">UI Touch (Jinja2)</h3>
                <p className="text-sm text-neutral-600">Cartella: <code>templates/</code><br/>Template HTML responsivi con pulsanti ad alto contrasto (index, carico, magazzino).</p>
              </div>

              <div className="bg-neutral-50 p-6 rounded-xl border border-neutral-200">
                <FileSpreadsheet className="w-8 h-8 text-green-600 mb-4" />
                <h3 className="font-bold text-neutral-900 mb-2">Export Excel (Pandas)</h3>
                <p className="text-sm text-neutral-600">Moduli <code>pandas</code> e <code>openpyxl</code><br/>Integrazione diretta su app.py per aggiornamento live a 3 fogli al salvataggio.</p>
              </div>
            </div>

            <div className="bg-blue-50 text-blue-900 p-6 rounded-xl flex items-start gap-4">
              <Download className="w-6 h-6 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-bold mb-1">Come avviare il progetto</h4>
                <ol className="list-decimal ml-5 text-sm space-y-1">
                  <li>Esporta i file da AI Studio (usa il menu in alto per scaricare ZIP).</li>
                  <li>Inizializza il DB PostgreSQL con il file <code>database.sql</code>.</li>
                  <li>Installa le dipendenze: <code>pip install flask psycopg2-binary pandas openpyxl python-dotenv</code>.</li>
                  <li>Avvia il backend: <code>python app.py</code> e apri il browser su <code>http://localhost:5000</code>.</li>
                </ol>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

