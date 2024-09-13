/** @type {import('next').NextConfig} */
const nextConfig = {
    async redirects() {
        return [
            {
                source: '/',
                destination: '/camera',
                permanent: false,
                has: [
                    {
                        type: 'cookie',
                        key: 'authToken',
                    },
                ],
            },
            {
                source: '/',
                destination: '/auth',
                permanent: false,
                missing: [
                    {
                        type: 'cookie',
                        key: 'authToken',
                    },
                ],
            },
        ];
    },
};

export default nextConfig;