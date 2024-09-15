"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { login, register } from "../api";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "react-hot-toast";

export default function AuthContent() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);
    const router = useRouter();
    const searchParams = useSearchParams();

    useEffect(() => setMounted(true), []);

    const handleSubmit = async (
        event: React.FormEvent,
        type: "login" | "register",
    ) => {
        event.preventDefault();
        try {
            if (type === "login") {
                const { access_token } = await login(username, password);
                localStorage.setItem("token", access_token);
                toast.success("Logged in successfully");
                const destination = searchParams.get("destination") || "/camera";
                router.push(destination);
            } else {
                await register(username, password);
                toast.success("Registered successfully. Please log in.");
            }
        } catch (error) {
            toast.error("Username or password is wrong, please try again.");
        }
    };

    if (!mounted) return null;

    return (
        <div className="flex flex-col items-center justify-center min-h-screen">
            <Button
                variant="outline"
                size="icon"
                className="absolute top-4 right-4"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
                {theme === "dark" ? (
                    <Sun className="h-[1.2rem] w-[1.2rem]" />
                ) : (
                    <Moon className="h-[1.2rem] w-[1.2rem]" />
                )}
                <span className="sr-only">Toggle theme</span>
            </Button>
            <Card className="w-[350px]">
                <CardHeader>
                    <CardTitle>Authentication</CardTitle>
                </CardHeader>
                <CardContent>
                    <Tabs defaultValue="login">
                        <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="login">Login</TabsTrigger>
                            <TabsTrigger value="register">Register</TabsTrigger>
                        </TabsList>
                        <TabsContent value="login">
                            <form onSubmit={(e) => handleSubmit(e, "login")}>
                                <Input
                                    type="text"
                                    placeholder="Username"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="mb-2"
                                />
                                <Input
                                    type="password"
                                    placeholder="Password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="mb-4"
                                />
                                <Button type="submit" className="w-full">
                                    Login
                                </Button>
                            </form>
                        </TabsContent>
                        <TabsContent value="register">
                            <form onSubmit={(e) => handleSubmit(e, "register")}>
                                <Input
                                    type="text"
                                    placeholder="Username"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="mb-2"
                                />
                                <Input
                                    type="password"
                                    placeholder="Password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="mb-4"
                                />
                                <Button type="submit" className="w-full">
                                    Register
                                </Button>
                            </form>
                        </TabsContent>
                    </Tabs>
                </CardContent>
            </Card>
        </div>
    );
}
