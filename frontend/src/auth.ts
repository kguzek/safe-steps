import { PrismaAdapter } from "@auth/prisma-adapter";
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

import { prisma } from "@/prisma";

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  providers: [
    Credentials({
      name: "Credentials",
      credentials: {
        username: {
          label: "Nazwa użytkownika",
          type: "text",
          placeholder: "jan.kowalski",
        },
        password: { label: "Hasło", type: "password" },
      },
    }),
  ],
});
