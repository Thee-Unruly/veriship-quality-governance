    def streamable_http_app(self) -> Starlette:
        """Return an instance of the StreamableHTTP server app."""
        from starlette.middleware import Middleware

        # Create session manager on first call (lazy initialization)
        if self._session_manager is None:  # pragma: no branch
            self._session_manager = StreamableHTTPSessionManager(
                app=self._mcp_server,
                event_store=self._event_store,
                retry_interval=self._retry_interval,
                json_response=self.settings.json_response,
                stateless=self.settings.stateless_http,  # Use the stateless setting
                security_settings=self.settings.transport_security,
            )

        # Create the ASGI handler
        streamable_http_app = StreamableHTTPASGIApp(self._session_manager)

        # Create routes
        routes: list[Route | Mount] = []
        middleware: list[Middleware] = []
        required_scopes = []

        # Set up auth if configured
        if self.settings.auth:  # pragma: no cover
            required_scopes = self.settings.auth.required_scopes or []

            # Add auth middleware if token verifier is available
            if self._token_verifier:
                middleware = [
                    Middleware(
                        AuthenticationMiddleware,
                        backend=BearerAuthBackend(self._token_verifier),
                    ),
                    Middleware(AuthContextMiddleware),
                ]

            # Add auth endpoints if auth server provider is configured
            if self._auth_server_provider:
                from mcp.server.auth.routes import create_auth_routes

                routes.extend(
                    create_auth_routes(
                        provider=self._auth_server_provider,
                        issuer_url=self.settings.auth.issuer_url,
                        service_documentation_url=self.settings.auth.service_documentation_url,
                        client_registration_options=self.settings.auth.client_registration_options,
                        revocation_options=self.settings.auth.revocation_options,
                    )
                )

        # Set up routes with or without auth
        if self._token_verifier:  # pragma: no cover
            # Determine resource metadata URL
            resource_metadata_url = None
            if self.settings.auth and self.settings.auth.resource_server_url:
                from mcp.server.auth.routes import build_resource_metadata_url

                # Build compliant metadata URL for WWW-Authenticate header
                resource_metadata_url = build_resource_metadata_url(self.settings.auth.resource_server_url)

            routes.append(
                Route(
                    self.settings.streamable_http_path,
                    endpoint=RequireAuthMiddleware(streamable_http_app, required_scopes, resource_metadata_url),
                )
            )
        else:
            # Auth is disabled, no wrapper needed
            routes.append(
                Route(
                    self.settings.streamable_http_path,
                    endpoint=streamable_http_app,
                )
            )

        # Add protected resource metadata endpoint if configured as RS
        if self.settings.auth and self.settings.auth.resource_server_url:  # pragma: no cover
            from mcp.server.auth.routes import create_protected_resource_routes

            routes.extend(
                create_protected_resource_routes(
                    resource_url=self.settings.auth.resource_server_url,
                    authorization_servers=[self.settings.auth.issuer_url],
                    scopes_supported=self.settings.auth.required_scopes,
                )
            )

        routes.extend(self._custom_starlette_routes)

        return Starlette(
            debug=self.settings.debug,
            routes=routes,
            middleware=middleware,
            lifespan=lambda app: self.session_manager.run(),
        )

