'use client';
import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useTheme } from "next-themes"
import { Moon, Sun } from "lucide-react"

export default function AuthPage() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const { theme, setTheme } = useTheme()
    const [mounted, setMounted] = useState(false)

    useEffect(() => setMounted(true), [])

    const handleSubmit = async (event: React.FormEvent, type: 'login' | 'register') => {
        event.preventDefault()
        // Handle login/register logic here
    }

    if (!mounted) return null

    return (
        <div className="flex flex-col items-center justify-center min-h-screen">
            <Button
                variant="outline"
                size="icon"
                className="absolute top-4 right-4"
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            >
                {theme === 'dark' ? <Sun className="h-[1.2rem] w-[1.2rem]" /> : <Moon className="h-[1.2rem] w-[1.2rem]" />}
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
                            <form onSubmit={(e) => handleSubmit(e, 'login')}>
                                <Input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="mb-2" />
                                <Input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className="mb-4" />
                                <Button type="submit" className="w-full">Login</Button>
                            </form>
                        </TabsContent>
                        <TabsContent value="register">
                            <form onSubmit={(e) => handleSubmit(e, 'register')}>
                                <Input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="mb-2" />
                                <Input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className="mb-4" />
                                <Button type="submit" className="w-full">Register</Button>
                            </form>
                        </TabsContent>
                    </Tabs>
                </CardContent>
            </Card>
        </div>
    )
}