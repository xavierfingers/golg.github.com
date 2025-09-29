using System;

class AdventureGame
{
    static void Main(string[] args)
    {
        Console.WriteLine("Welcome to The Cave of Whispers!");
        Console.WriteLine("You stand at the entrance of a dark cave. Faint whispers echo from within.");
        Console.WriteLine("What do you do?");
        Console.WriteLine("  A) Enter the cave.");
        Console.WriteLine("  B) Walk away.");

        string choice1 = (Console.ReadLine() ?? "").ToUpper();

        if (choice1 == "A")
        {
            Console.WriteLine("\nYou enter the cave. The entrance collapses behind you! The whispers grow louder.");
            Console.WriteLine("What do you do?");
            Console.WriteLine("  A) Follow the whispers.");
            Console.WriteLine("  B) Look for another way out.");

            string choice2 = (Console.ReadLine() ?? "").ToUpper();

            if (choice2 == "A")
            {
                Console.WriteLine("\nYou follow the whispers and find a glowing crystal, the source of the sound.");
                Console.WriteLine("The crystal offers you a choice: take it and gain its power, or leave it.");
                Console.WriteLine("What do you do?");
                Console.WriteLine("  A) Take the crystal.");
                Console.WriteLine("  B) Leave the crystal.");

                string choice3 = (Console.ReadLine() ?? "").ToUpper();

                if (choice3 == "A")
                {
                    Console.WriteLine("\nYou take the crystal and feel a surge of power. You find a hidden exit and emerge from the cave, ready for new adventures!");
                    Console.WriteLine("Congratulations, you have won!");
                }
                else if (choice3 == "B")
                {
                    Console.WriteLine("\nYou leave the crystal. The whispers fade, and you find a hidden exit, emerging from the cave unchanged.");
                    Console.WriteLine("You survived, but the mystery of the cave remains.");
                }
                else
                {
                    Console.WriteLine("\nInvalid choice. The crystal's light fades, and you are lost in the darkness forever.");
                }
            }
            else if (choice2 == "B")
            {
                Console.WriteLine("\nYou get lost in the dark and wander for what feels like an eternity. You are never seen again.");
                Console.WriteLine("Game Over.");
            }
            else
            {
                Console.WriteLine("\nInvalid choice. You hesitate for too long and are consumed by the darkness.");
                Console.WriteLine("Game Over.");
            }
        }
        else if (choice1 == "B")
        {
            Console.WriteLine("\nYou walk away and go home, forever wondering about the secrets of the cave.");
            Console.WriteLine("The end.");
        }
        else
        {
            Console.WriteLine("\nInvalid choice. You stumble and fall, hitting your head on a rock. The world goes dark.");
            Console.WriteLine("Game Over.");
        }
    }
}
