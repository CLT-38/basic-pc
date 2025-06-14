print("Début du script pilot.py...") # Ligne de débogage ajoutée

import asyncio
import time
from bleak import BleakScanner, BleakClient
import keyboard # Ajout de l'import pour la gestion du clavier

# UUIDs du service Nordic UART (NUS) et de ses caractéristiques
NORDIC_UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
# Caractéristique RX : le central (PC) écrit dessus, le périphérique (Arduino) lit
NORDIC_UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
# Caractéristique TX : le périphérique (Arduino) écrit dessus, le central (PC) lit/notifie
# NORDIC_UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" # Non utilisé pour l'écriture depuis le PC

async def run():
    print("Recherche des appareils BLE...")
    devices = await BleakScanner.discover()

    if not devices:
        print("Aucun appareil BLE trouvé.")
        return

    print("Appareils trouvés :")
    for i, device in enumerate(devices):
        print(f"{i}: {device.name} ({device.address})")

    if not devices:
        return

    while True:
        try:
            choice = int(input("Entrez le numéro de l'appareil à connecter : "))
            if 0 <= choice < len(devices):
                selected_device = devices[choice]
                break
            else:
                print("Numéro invalide. Veuillez réessayer.")
        except ValueError:
            print("Entrée invalide. Veuillez entrer un nombre.")

    print(f"Connexion à {selected_device.name} ({selected_device.address})...")

    async with BleakClient(selected_device.address) as client:
        if client.is_connected:
            print("Connecté avec succès !")

            # Vérifier si le service NUS est présent
            nus_service = None
            for service in client.services:
                if service.uuid.lower() == NORDIC_UART_SERVICE_UUID.lower():
                    nus_service = service
                    break
            
            if not nus_service:
                print(f"Le service UART Nordic (UUID: {NORDIC_UART_SERVICE_UUID}) n'a pas été trouvé sur l'appareil.")
                return

            # Vérifier si la caractéristique RX est présente
            rx_char = nus_service.get_characteristic(NORDIC_UART_RX_CHAR_UUID.lower())
            if not rx_char:
                print(f"La caractéristique RX (UUID: {NORDIC_UART_RX_CHAR_UUID}) n'a pas été trouvée.")
                return

            print("Utilisez les touches fléchées pour contrôler le robot.")
            print("Flèche Haut: 8, Flèche Bas: 2, Flèche Gauche: 4, Flèche Droite: 6")
            print("Appuyez sur 'q' pour arrêter et déconnecter, ou Ctrl+C pour quitter.")
            
            interval = 0.1  # secondes, intervalle de vérification des touches

            try:
                while True:
                    command_to_send = None 
                    
                    if keyboard.is_pressed('up arrow'): # Utilisation de 'up arrow' pour plus de clarté
                        command_to_send = 8
                    elif keyboard.is_pressed('down arrow'):
                        command_to_send = 2
                    elif keyboard.is_pressed('left arrow'):
                        command_to_send = 7
                    elif keyboard.is_pressed('right arrow'):
                        command_to_send = 9
                    
                    if keyboard.is_pressed('q'): 
                        print("Touche 'q' pressée. Arrêt des commandes...")
                        break 

                    if command_to_send is not None:
                        print(f"Envoi de la commande : {command_to_send}")
                        data_to_send = bytearray([command_to_send])
                        await client.write_gatt_char(rx_char.uuid, data_to_send, response=True)
                        # print("Commande envoyée.") # Optionnel pour moins de verbosité
                    
                    # Si aucune touche fléchée n'est pressée, aucune commande n'est envoyée.
                    # Le robot pourrait continuer sa dernière action ou s'arrêter (selon sa programmation).
                    # Pour un arrêt explicite, il faudrait envoyer une commande "stop" (ex: 5) ici.

                    await asyncio.sleep(interval) 
            
            except Exception as e:
                print(f"Erreur pendant la boucle de commande : {e}")
            
            print("Fin de la session de contrôle.")

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Programme interrompu par l'utilisateur.")
